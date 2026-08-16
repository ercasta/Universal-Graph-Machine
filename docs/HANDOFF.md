# Handoff — 2026-08-15 (quiescence as rules, and §7's test)

Branch `restart`. **549 checks, 0 failing.** New gate `python -m ugm.quiescence`: **137 candidates
compared, 0 disagreeing, 5/6 of its own rules exercised.** `ugm.agreement` 28/0 with 7/7 exercised,
and **1.2s where it was 118s**; every other instrument green (`vocabulary` 18/0 with `asked` added).

**Read `docs/observations.md` Parts 6 and 7** — 6 is quiescence as rules and what it found, 7 is the
fix the author authorised and the three things that fell out of it.

## The blocking question is answered: no new primitive

The rewrite was blocked on whether `_would_change` needs §4's missing aggregate. **It does not.**
§4's gap is a claim about a set of **entries**, where a `-` member can only say *an entry denies
this*. Quiescence's universal — *no conclusion of this application would change anything* — ranges
over **structure**, where a `-` member can only mean *not derived*. That is the universal wanted, for
free. Quiescence is six rules; the harness hands over the grounded conclusion, its locus and the
seat, and never the verdict.

**So the rewrite target is fully specified. Start it.** The only branch that needs something new is
`_forbid`: it unifies a stored generic pattern against the proposition, and `unifies(?pat, ?prop)` is
not a structural relation a rule can ask.

## §7's test was asking the wrong question in three places

*Does a variable appear anywhere inside this node* is not *did this member leave a variable of its
own unbound*. The difference is every fact the chain deposits about a **mention** — a reified rule's
proposition is a pattern, so the entry node carries its variables, and so did every `mentioned`,
`in_delta` and `delta_next` fact about it. Measured before the fix: **97 of 125 `mentioned` and 175
of 216 `delta_next` facts invisible to the matcher**, and with them the rule-level read was wrong
wherever a generic entry sat between two revisions in one delta.

Fixed in `_as_fact` (binds a variable to a variable), `_left_open` (`_mint_structure`), and `_ground`
(a variable bound to a value anchors its member). Two guards came with it, both cases match could not
previously produce: **a member finding itself** — interning puts a rule's own member among the
instances of its relation, and `unify` short-circuits on identity — and **a rule reading its own
reification**, which binds `?pat` to `echoed(?pat)` and builds a structure containing itself.

## The read was quadratic, and the blindfold was what hid it

With the reified entries visible, `agreement`'s five-moment fixture derived 2,062 `cand` facts and
stopped finishing: 4.4M unifications in 60 seconds, which is 2,062 squared. Three fixes, in order of
how much they bought:

- **the read is a question, so ask it about something.** `ask_read` seeded only `asking(<seat>)`, so
  the read answered about every proposition in the chain. `asked(<prop>)` is the missing half:
  **10,638 derived facts and 90.3s → 61 facts and 0.3s.**
- **an argument-position index over structural instances** (`Graph._by_arg`) — the entry side took
  this when the option-set quadratic was found; the structural side never had it. *A join is not a
  scan*, in the half of the matcher the first fix did not touch.
- **two memos**, `occurs` (6.0M calls) and `_vars_in` (2.7M). The second arrived with its own trap
  and the suite caught it: a node id means nothing outside the graph that minted it, so a
  module-level cache answered one machine with another machine's node.

The suite is **11.5s against 13.1s** before all of this, so the visibility was paid for and change
was returned.

## A table-driven loop, first version — `python -m ugm.attention`

The author's design, built beside the shipped loop rather than in it: a score per rule, apply the
highest-scoring rule whose antecedent matches, then run that rule's postconditions (query → buff) to
move the table. Declaration order is the tiebreak — which is §18's rule already. `standing` seeds the
default table; every other rule sits at the floor, so nothing is dead. Buffs are supplied from Python
so the `after { … } => boost(<R>, n)` surface stays open. Every buff is traced as
`(tick, by, target, delta, frozen)` and the trace is held to the live table on every run.

**The penguin case works, and it needed one postcondition.** Same corpus, same declaration order,
`<flies>` declared before `<flightless>`:

| | applied | concluded |
|---|---|---|
| declaration order alone | `classify`, `flies` | `can_fly(pingu)` |
| one buff, `+20` on `<flightless>` | `classify`, `flightless` | `grounded(pingu)` |

No defeat relation, no `unless`, no precedence claim. **But ordering alone is not defeasibility**, and
running it is how that showed: a loop that continues to quiescence applies *both* rules whatever the
order, because a low score delays a rule and never removes one — and removal is what this design
refuses on purpose. What turns an order into a default is **stopping**: ask, take the first rule that
matches, act. So *completion is the output of a rule* is not a detail of the design; it is what makes
a score mean anything.

**Against the shipped loop, on three corpora** — conclusions reached, by relation:

| corpus | ticks (shipped / table) | only shipped | only table |
|---|---|---|---|
| `delay.ugm` | 11 / 9 | `close` x15, `quiet` x1 | — |
| `worked.ugm` | 12 / 6 | `close` x4, `left` x2, `quiet` x1 | `spent` x2, `rain`, `raining` |
| `quest-p1.ugm` | 18 / 10 | `spent` x6, `exercised` x4, `verdict` x3, `pursued` x2, `quiet`, `emitted` | — |

Read it as the work list rather than as a failure. `close` is doubt — a record that exists only
because the shipped tick materialises an option set, and by the author's argument it should not
exist. `quiet`, `left`, `verdict`, `emitted` are the other half: the shipped tick does five things
besides choosing (`_enough`, `_leave`, `_wake`, `_widen`, `_recover`), and this loop does none of
them, so `quest-p1` never acts and `worked` never exits its supposition. **Those five are exactly the
rules the design says should carry reset-buff postconditions**, and the diff says which conclusions
each is responsible for.

**Cost is not measurable at this size** — both loops are hundredths of a second, and the table loop
matched 219 rules over 9 ticks on `delay`. The saving the design predicts is real only where the pool
is large and the table is small; a corpus big enough to show it does not exist here yet.

### ...and doubt as an occasion, not a record

The author's second correction: the loop does not hold a tick waiting for doubt to resolve, because
a **settling rule fires**. So depositing the doubt IS the move, `<settle-doubt>` gets the next turn,
and what it does is spend attention -- the settlement is a buff like any other, calibratable rather
than a branch. A corpus replaces it by writing a rule that outscores it (ask the user, apply a
domain criterion). The backstop needs no semantics: if nothing settles, restating the doubt changes
nothing, so quiescence lets the winner apply and a corpus without a settling rule loses one tick
rather than the loop.

The window is a **prefix scan**: scores only fall down the table, so once a match is found at `s`,
everything below `s - tolerance` is irrelevant *without being matched*. The count knob is a guard
against a pathological table, not the mechanism. `?a` in `boost(?a, 1)` is the winner as the doubt
named it -- writable only because rules are subjects here and `_note` deposits `close` as a mention.

With doubt on, over the three corpora: **7/27, 3/13 and 7/28 moves raised a doubt, window never
wider than 3**, and the `close` records the first version dropped come back -- `delay` went from 15
missing to 4. The price is visible in ticks (9 -> 20 on `delay`), because a doubt costs a move and
settling costs another.

**The penguin, with the settling rule in place:**

| | doubts | applied | first answer |
|---|---|---|---|
| declaration order alone | 1 | `classify`, `settle-doubt`, `flies`, `flightless` | `can_fly(pingu)` |
| one buff, `+20` | 0 | `classify`, `flightless`, `flies` | `grounded(pingu)` |

Both rules still fire eventually -- ordering is not defeasibility, and that is the boundary above.
What the buff decides is **which answer comes first**, and whether the agent hesitates at all.

### The mechanism validates: same conclusions, three corpora

Adding two lines to the loop -- when the window is empty, say `quiet(<seat>)`, and if that changes
nothing, move the register (`_leave`) -- closes the gap:

| corpus | ticks (shipped / table) | missing | doubts / moves |
|---|---|---|---|
| `delay.ugm` | 11 / 20 | **4**, all `close` | 7 / 27 |
| `worked.ugm` | 12 / 11 | **0** | 3 / 14 |
| `quest-p1.ugm` | 18 / 27 | **0** | 7 / 34 |

`quest-p1` acts again -- the emission, the verdict, `pursued`, `blocked`. Nothing about goals was
written: the bundle's rules were simply never given their turn, because `quiet` is what they react to
and the first version never said it. The four remaining differences on `delay` are `close` records
about rivals outside the window, which is the bounded comparison working as designed rather than a
loss.

What the engine knows, in full: a score per rule, the first match, the window, deposit a doubt,
deposit `quiet`, move the register. No goal, no completion, no widening -- `_widen` and `_recover`
did not have to be rewritten as rules because a table has no shortlist to widen.

The table loop takes more ticks (a doubt costs a move and settling costs another) and the same
wall-clock to a hundredth of a second. Cost is still unmeasurable at this size: the saving the design
predicts needs a pool large enough that not matching most of it matters.

### The dungeon answers the cost question, and the answer is not the expected one

`ugm.dungeon` is the largest corpus here -- 21 rules of its own, three tools, a fight that takes
tens of moves. It cannot be loaded from the file alone (`<dice>`, `<arith>` and `<beats>` are
answerers registered in Python), so the machine is built the way `ugm.dungeon` builds it and only the
loop differs.

| | shipped | table |
|---|---|---|
| moves | 148 | 165 |
| seconds | **0.31** | **0.26** |
| conclusions | 726 | 765, missing **1** (`defeated`) |
| doubts | -- | 17 of 182 moves, window never wider than 3 |

So the table loop is already slightly faster on a real corpus while reaching the same conclusions.
**But not for the predicted reason, and this is the number to keep:** it matched **36.8 rules per
move** out of a pool of ~38. Stopping at the first match saves nothing yet, because the table is
FLAT -- every corpus rule sits at the floor, so the scan walks almost the whole pool before it finds
anything. What the run saves is the option set and the arbitration over it, not the matching.

That makes the metric for calibration precise and cheap to watch: **rules matched per move**. It is
36.8 today; every postcondition that lifts the right rule pulls it down, and if learning cannot move
it, the design's central performance claim is unsupported. No corpus here has a table worth reading
yet, which is exactly what the learning work is for.

### The surface exists

```
rule <classify> = implies( { +asked(?x) }, { +considered(?x) } )
  after { +penguin(?x) } => boost(<flightless>, 20)

rule <settle-doubt> = implies( { +close(?a, ?b) }, { +settled(?a, ?b) } )
  frozen after => boost(?a, 1)
```

`after` takes an ordinary antecedent -- no new notation, the same matcher -- and it is matched with
the application's own bindings already substituted in, which is what makes it a POSTcondition rather
than a second rule. A bare `after` has no query and always holds. `boost` and `damp` name a rule or
a variable the query bound; `frozen` marks what a calibration process may not touch and changes
nothing about how the clause runs. Parsed by `text.py`, stored on `Rule.posts`, read only by a loop
that has a table -- the shipped loop never looks at it.

The penguin, with everything now in the corpus and nothing in Python:

| | doubts | applied | first answer |
|---|---|---|---|
| declaration order alone | 1 | `classify`, `settle-doubt`, `flies`, `flightless` | `can_fly(pingu)` |
| with the postcondition | 0 | `classify`, `flightless`, `flies` | `grounded(pingu)` |

### Score first, match only the top -- and a negative result about learning

The author's optimisation: score decides WHO is matched, so a rule below the cut costs nothing at
all. A shortlist of five is matched; if nothing in it applies, the shortlist **widens** -- which is
the shipped guarantee, *a dry shortlist is not a finished search*, and it is what stops a miss in the
top five from depositing `quiet` while work remained. Worst case is exactly the old cost; best case
is five.

| corpus | matched/move | widenings | seconds (shipped / table) | conclusions lost |
|---|---|---|---|---|
| `delay.ugm` | 25.1 | 66 | 0.01 / 0.01 | 11, all `close` |
| `worked.ugm` | 35.0 | 66 | 0.02 / 0.02 | 2, all `close` |
| `quest-p1.ugm` | 17.7 | 67 | 0.01 / 0.01 | **0** |
| `dungeon` | 29.6 (was 36.8) | 862 | 0.28 / 0.22 | 5: four `close`, one `defeated` |

**No substantive conclusion is lost anywhere** -- every difference is a doubt record about a rival
the bounded window never looked at. But 862 widenings over 174 moves is about five per move: the top
of the table is occupied by rules that do not match. The `standing` default puts the bundle there,
and the bundle is exactly the reactive half -- intake, watchdogs, `<give-up>` -- which fires on rare
occasions by design.

**And the cheapest possible calibration makes it worse, which is the useful part.** `reflex` damps
every rule tried without matching and boosts the one that applied -- no model, no gold, no human,
using only what the loop finds out for free:

| | moves | matched/move | conclusions |
|---|---|---|---|
| off | 161 | 29.6 | 753 |
| on | 116 | 29.0 | **628** |

It barely moved the number and it lost 125 conclusions, because **tried-and-missed is not evidence a
rule is unimportant** -- it is evidence the rule was not applicable *in that state*. Damping it
globally starves the situational rules, which is most of a corpus. The signal has to carry the
state, and carrying the state is exactly what a postcondition's query does. So the negative result
argues for the author's design rather than against it: learning must calibrate **when** to boost, not
how much to weigh a rule in general.

That also makes the training target sharper. `matched/move` is not moved by weights alone; it is
moved by conditional buffs that put the right rule on top *in the situations where it applies*.

### Teaching from use -- `python -m ugm.teaching`

The author's framing: *a human is the first, manual user of the KB*. Not a labelling task beside the
system -- the ordinary first use, by a person stepping the corpus and picking the next rule. They are
doing what the table will later do, so what they leave behind IS the table. Two signals come out of
that use and only one is calibration: **the wrong order** (a buff) and **none of these fits** (a
missing rule, which no calibration supplies).

The mechanism is validated without a human, because the shipped loop's arbitration is a teacher that
is right by construction: it chooses over the full option set at every step, deterministically. If
bootstrapping cannot imitate that, it will not learn from a person either.

| | teacher took the table's top | moves | matched/move | agree with teacher | conclusions lost |
|---|---|---|---|---|---|
| `quest-p1` uncalibrated | **21/21** | 21 | 17.7 | 21 | 0 |
| `quest-p1` after teaching | | 18 | 8.1 | 12 | **9** |
| `dungeon` uncalibrated | **5/149** | 161 | 29.6 | 7 | 0 |
| `dungeon` after teaching | | **400 (the limit)** | **6.2** | 50 | **84** |

**The cost claim moved for the first time: 29.6 to 6.2 matched per move**, and agreement with the
teacher went 7 to 50. So a taught table does put the right rules on top, which is the whole
performance argument.

**And unconditional bigrams are unsafe.** The dungeon ran away to the tick limit and lost 84
conclusions; `quest-p1`, which already agreed with the teacher on every move, was made worse by being
taught. A boost with no query never stops applying, so `A` lifts `R`, `R` lifts `A`, and the loop
finds work for ever.

That is the **third** independent result pointing at one conclusion. The reflex damped what missed
and lost 125 conclusions; the reflex barely moved the cost; the bigram moves the cost and breaks the
behaviour. All three fail in the same place: they say how much and never **when**. The query in
`after { ... } => boost(...)` is not an elaboration of the design, it is the part that makes it
work -- and anti-unification over the situations a choice was taught in is how a query gets written.

⚠ `quest-p1` is not a teaching corpus: the uncalibrated table already reproduces the teacher's
sequence exactly, and a fixture that cannot lose cannot measure. The dungeon is the one to work on.

Two measurement bugs were found and fixed while building this, both of the recorded kind: agreement
compared **application identity** where it meant the rule, and reported 0/149 -- which reads as *the
table is never right* and meant *the comparison cannot be right*; and the watcher ran at the CHOICE
rather than after the move, so a tick that deposited a doubt and applied nothing still taught a
bigram for a move that never happened.

### The query, by anti-unification -- and it is the first calibration that does not break anything

Anti-unification is the dual of `unify`: unify goes down (what substitution makes these the same),
this goes up (what is the least general thing both are instances of). Where two examples agree the
structure is kept, where they differ a variable appears, and **the same disagreement gives the same
variable everywhere** -- `generalise` in `rules.py`, which already existed for *an example becomes a
rule*.

What a demonstration becomes: the entries the taught rule CONSUMED -- what made the move available,
not the whole state -- with the previous rule's own bindings folded back in, so the query says *this
orc* rather than *some orc*. Then anti-unified across every demonstration of the same pair. Two
guards: a member that generalises to a bare variable is dropped as saying nothing, and a query that
also holds where the teacher chose **otherwise** after the same rule is dropped as too general. The
negatives are free -- the teacher's own run recorded them.

**The dungeon, taught by the shipped arbitration:**

| | posts | moves | matched/move | moves agreeing with the teacher | conclusions lost |
|---|---|---|---|---|---|
| untaught | -- | 161 | 29.6 | 7 | 0 |
| bigram (no query) | 31 | **400 (the limit)** | **6.2** | 50 | 84 |
| with a query | 25 | **149** (the teacher's own count) | 25.8 | **93** | **11** |

Agreement went from **7 of 161 to 93 of 149**, the runaway is gone, and the loss fell from 84 to 11.
Five queries were dropped for holding where the teacher disagreed, which is the collision check doing
real work.

**And the speed came back out.** 6.2 matched per move was the bigram boosting indiscriminately; with
a query the table is flat again most of the time, and the gain is only 29.6 to 25.8. That is the
honest shape of the trade: **an unconditional buff is fast and wrong, a conditional buff is right and
barely faster.** Getting both is what the author's *buffs persist until a refocus resets them* is
for -- a lifted rule has to stay lifted for the next few moves, not for one.

**One lesson could not be written down.** A sign atom renders as `+`, and `+` opens a member, so a
premise mentioning one is a fact the graph holds and the surface cannot say. Counted rather than
worked around: a calibration nobody can read cannot be argued with or frozen, which is the whole
reason it belongs in the corpus.

⚠ And teaching a corpus that is already right makes it worse. On `quest-p1` the untaught table
reproduces the teacher on all 21 moves; teaching costs 9 conclusions with bigrams and 12 with
queries. Calibration should be gated on disagreement -- there is nothing to learn where there is no
disagreement, and something to lose.

⚠ The lesson crosses machines as an **utterance**: node ids mean nothing outside the graph that
minted them, so a query is rendered as text on the teacher's machine and re-read in the student's own
name scope. That is `ugm/table.py`'s rule for what may cross between agents, arriving from the
learning side -- and it makes a lesson a document: savable, diffable, and loadable into a corpus that
was never taught.

### Buffs that expire, saturate, and can be reset -- and the cost claim still does not move

**Sigmoid: at read time it is a no-op.** The table is used only to order rules and to measure
closeness, and a monotone transform cannot change an ordering. What was wanted is saturation at the
UPDATE -- a boost that shrinks as a rule is already lifted, which is the sigmoid's derivative rather
than the sigmoid. The evidence was already in the last run: the taught runaway fired **0 doubts**
against 13 untaught, because scores had inflated until nothing was ever within `tolerance` of
anything. A fixed tolerance only means something against a stable scale.

Three things built, all small:

* **a buff lives** (`LIFE`, 12 moves) and the score is DERIVED from the live buffs and the defaults,
  so nothing has to be undone when one expires. A lift is about what is going on now; what survives
  is the postcondition, which re-applies whenever its query holds again.
* **saturating updates** (`MAX_LIFT`): a rule at the ceiling gains nothing from being taught again.
* **`reset`**, a third postcondition verb beside `boost` and `damp`: back to the default table. The
  author's refocusing mechanism, and nothing in the engine knows what a goal is -- deciding when to
  refocus is a rule's business.

| dungeon, taught | moves | matched/move | agree with teacher | lost | doubts |
|---|---|---|---|---|---|
| untaught | 161 | 29.6 | 7 | 0 | 13 |
| bigram, before this | 400 (limit) | 6.2 | 50 | 84 | **0** |
| bigram, now | 198 | 14.0 | 58 | 134 | 10 |
| query, before this | 149 | 25.8 | 93 | 11 | 1 |
| **query, now** | **148** | 28.5 | **105 of 149** | **10** | 0 |

Agreement is now **70%** of the teacher's moves, the runaway is gone from both variants, and doubt
survives. **But `matched/move` has not moved: 29.6 untaught, 28.5 taught.** Lowering the `standing`
default from 10 to 5 buys 24.7 with no other change, and to 1 buys 24.3 while losing conclusions --
so the default table is mildly miscalibrated and that is not where the cost is either.

**The reason is structural, and it is the next thing to fix.** A bigram lifts a rule for the move
after a *specific predecessor*. Most moves have no lifted candidate at all, so the scan is unguided
and pays the full pool. To make the cost claim true, a lesson has to say *in situations like this,
these rules are worth trying* -- keyed on the **situation** rather than on what fired last. The
machinery is already there: the query is a situation, so the same anti-unification can hang a buff
off the state instead of off a predecessor.

### Keying the lesson on the situation -- built, measured, and it does not work for a reason

The plan was: key a lesson on the situation rather than on the predecessor, as a learned recogniser
that concludes `noticing(<R>)` and hangs the buff off itself. Built, and two things had to be fixed
before it could be judged at all.

**The metric was wrong, and it said the mechanism destroyed the behaviour.** A learned recogniser and
a settled doubt are moves the teacher never made, so they shift everything after them and a
positional comparison counts one insertion as a hundred disagreements: it reported **5 of 149**.
Aligned as a longest common subsequence, with the bookkeeping moves dropped, the same run scores
**148 of 149**. The measurement trap this repo keeps recording, in a new place.

**And experience means more than one fight.** Generalising over two runs of the SAME fight keeps
`goblin1`, because both examples really do contain it -- `generalise` is right and the evidence is
thin. Teaching from four fights with different seeds turns the constants into variables:
`swing <= attack(?a, ?b, ?c)`, `harm <= hits(?a, ?b, ?c), die(?a, ?d)`.

| dungeon, taught from four fights | posts | moves | matched/move | agrees (LCS) | lost | doubts |
|---|---|---|---|---|---|---|
| untaught | -- | 161 | 29.6 | -- | 0 | 13 |
| **bigram** | 41 | 158 | **14.2** | 140 / 149 | 10 | 10 |
| bigram + query | 19 | 151 | 28.0 | **148 / 149** | **0** | 3 |
| situation recogniser | 15 | 157 | 30.3 | 148 / 149 | 0 | 7 |

**The recogniser fires 2 times out of 16 installed, and the reason is structural.** A recogniser
whose query is the target's own premises cannot fire before the target is applicable -- so it was
rekeyed on the PRECURSOR, the state one move earlier, which took it from 1 in 19 to 2 in 16. Still
nothing, and now the reason is clear: **in a one-move-per-tick loop, spending a move on recognition
competes with doing the work.** The recogniser's premises are exactly what makes the precursor rule
applicable, so the precursor wins the scan and the recogniser never gets its turn.

Which says where situation-keyed lessons have to live: **not in a rule, but in a postcondition** --
something evaluated for free after whatever applied, rather than something that must win a move to be
heard. And the cheap version of *evaluated after whatever applied* is the bigram, where the
predecessor acts as an index into when the query is worth checking.

**So the best operating point measured is the plain bigram with decay and saturation**: `matched/move`
29.6 to **14.2**, 140 of 149 moves reproduced, 10 conclusions lost. The cost claim is delivered; what
it costs is those ten conclusions and three fewer doubts. Adding the query buys them back and gives
the speed away, because a discriminating query is in force far less often. That is a real curve
between *how often the lift is in place* and *how often it is right*, and it is now measurable on
both axes.

### Triggers moved out of rules, and rerankers -- with the honest cost accounting

Two changes, both the author's:

**Experience is a separate document.** `after <A> { ... } => boost(<R>, n)` is now a statement of its
own, not a clause hanging off a rule declaration, and `Rule.posts` is gone -- the triggers live in
`RuleSet.triggers`, keyed by the rule they follow. What a rule MEANS and when it is worth reaching
for are different claims; a corpus loads its experience or does not.

**And the trigger still shares the rule's variables**, which is what makes the move a separation of
concerns rather than a change of meaning: the loader seeds the trigger's scope from the host rule's
own variables, so `after <swing> { +wounded(?b) }` is *that* `?b`. An inline clause had this for free
by being parsed inside the same statement; now the scope is handed to it instead. A name the rule
does not use is an ordinary fresh variable, which is what a `when` trigger has for all of them.

**Rerankers** are the second form: `when { ... } => boost(<R>, n)`, matched at ranking time, belonging
to no rule, and **ephemeral** -- recomputed every move and kept nowhere, so there is no decay to tune
and no runaway to guard against. That is the honest difference between the two kinds of attention:
what I was doing persists and fades, what is in front of me is recomputed.

This is also where the situation-keyed lessons belong, and running them as rules is what proved it: a
learned recogniser had to WIN A MOVE to be heard and fired twice out of sixteen. As a reranker it is
heard without winning anything, costs no move, and adds nothing to the pool.

| dungeon, taught from four fights | posts | moves | matched/move | agrees (LCS) | lost | doubts |
|---|---|---|---|---|---|---|
| untaught | -- | 161 | 29.6 | -- | 0 | 13 |
| bigram | 39 | 158 | **14.2** | 140 / 149 | 10 | 10 |
| bigram + query | 19 | 151 | 28.8 | 147 / 149 | 3 | 3 |
| situation, as rerankers | 15 | 151 | **42.7** | **148 / 149** | 3 | 3 |

**And the reranker costs more than it saves, which the cost column says because it was made to.** A
reranker query is a match like any other, so all fifteen are counted: fifteen extra matches per move
on top of a scan that did not shrink. Reporting a saving that was only moved between columns is the
trap this file has already recorded twice, and the number is 42.7 precisely because it was not
allowed to happen here.

The fix is the one `_forbid` already uses for norms: **index the triggers by what they mention and
consult only those a fresh fact could satisfy** -- delta-driven reranking, so a trigger about wounds
costs nothing on a move about doors. That is the next thing to build, and the column to watch is the
same one.

### The reranker works on the shortlist only -- and that decides what each mechanism is FOR

The author's restriction: a reranker looks at the options in front of the agent and nudges them. It
cannot pull a rule in from the bottom of the table -- widening is what reaches those, and a reranker
applies to each shortlist as it is reached. Implemented with `_forbid`'s own trick one level up:
triggers are indexed by the rule they lift, so a trigger about wounds costs nothing on a move about
doors, and only the ones targeting a shortlist member are consulted.

**And it has a consequence that is worth more than the cost saving: a reranker cannot shorten the
scan.** Which chunks get scanned is decided by the base table before any reranker runs. So:

| the two kinds of attention | decides | what it buys |
|---|---|---|
| `after <A> ... => boost` -- persistent, decays | **who is in** the shortlist | speed |
| `when { ... } => boost` -- ephemeral, per shortlist | who wins **inside** it | accuracy |

Measured on the dungeon, taught from four fights:

| | posts | moves | matched/move | agrees (LCS) | lost | doubts |
|---|---|---|---|---|---|---|
| untaught | -- | 161 | 29.6 | -- | 0 | 13 |
| persistent, unconditional | 39 | 158 | **14.2** | 140 / 149 | 10 | 10 |
| persistent, with a query | 19 | 151 | 28.8 | 147 / 149 | 3 | 3 |
| rerankers only | 15 | 155 | 39.5 | **148 / 149** | **0** | 7 |
| both | 54 | 158 | 19.4 | 140 / 149 | 10 | 10 |

**They do not compose yet, and the reason is the scale.** A persistent lift runs to the saturation
ceiling, so the reranker's nudge is added to a number that has already decided the order and changes
nothing: *both* scores exactly what the persistent half scores, 140 and 10 lost, while paying the
reranker's cost.

The fix is to stop adding them. Inside a shortlist the reranker should decide the ORDER and the base
score should only break its ties -- experience of the moment outranking accumulated habit, rather
than being summed with it. Ordinal within the chunk, cardinal outside it, which is the same split
this design has taken before (`doubt-is-a-tie`: a cardinal score beside an ordinal grade, never added
to it).

## What is left on this thread

- **`<silent>` is blind and should stay printed as blind.** A conclusion generic and *not* a mention
  cannot be written in the surface — the loader refuses it — so only `adopt`/`compose` reach that
  branch of `_decide_change`. Something should be able to.
- **`Rule.mentions` is the one input still not in the graph.** `reify` records members, loci and `as`
  names, not this, so a rule read back out of the graph loses it.
- Consider whether `_decide_change` should use `_left_open` too, and `_is_mention` retire with it.
  The gate can measure the difference; it was not attempted here.

## Still on the list, unchanged

Five pure deletions (`Frame.state`, `Step.state`, `_bookkeeping`'s 50-name set, `Rule.connective`'s
Python copy, `RuleSet.composed_from`), and one definition-plus-gate each for `at_or_after` (smallest,
start there), `scope_of`, `_recall`, `discharge`, `_forbid`, `_priority`, refraction. Four worked
gates to copy: `ugm.state`, `ugm.arbitration`, `ugm.agreement`, `ugm.quiescence`.

---

# Handoff — 2026-08-15 (the line between Python and rules)

Branch `restart`. **549 checks, 0 failing**. `ugm.vocabulary` 18/0 with **0 reserved names about a
world**; `ugm.agreement` 28/0, 7/7 rules exercised.

**Read `docs/observations.md` first.** It is this session's whole record — an audit of what lives only
in Python, five rounds of design argument with the author, and every experiment run with its result,
including the ones that came back negative and the three places I was wrong and corrected in place.

## The decision the session ended on

The author drew the line, and it is now the project's rule:

> Python may hold things that make the world **sayable** and **efficiently executable** — the
> substrate, and semantic-free accelerators over it (find a node labelled `moment`, walk `pred`, count
> descendants, unify). **Everything else is rules.** No logic, no concept classes. An entry is a graph
> node too.

There is no middle tier. What looked like one — `resolve`, `at_or_after`, `scope_of` — **splits**:
tier 1 supplies the walk or the ordering, tier 3 decides what it means.

The circularity that seemed to forbid this is not real. `ugm.agreement`'s rule-level read matches
against the **raw chain** (`anc`, `in_delta`, `entry_of`, `delta_next`, negation-as-failure on
structural members), not against the resolved state. So the read as rules runs on tier 1 alone — and
it already exists, as seven rules that agree with `Chain.resolve` on every comparison and are each
kill-probed.

## THE NEXT TASK, and it is one thing

**Write quiescence (`_would_change`) as rules.**

It is the smallest of the three aggregate-needing definitions and the most load-bearing — it is what
stops every loop. The rewrite the author wants (a kernel of ~800–1,200 lines against today's 5,300)
is blocked on one unknown: several tier-3 definitions may not be expressible today, because
`_recall`, `_would_change` and `_choose` are all **aggregates over a set of matches**, and a rule sees
one binding at a time.

- If quiescence can be written with what exists — structural relations, negation as failure, and the
  locus trick in observations §4.6 — the rewrite target is fully specified and the kernel is a clean
  job.
- If it cannot, that is the one primitive the kernel needs, and it gets added once, at the bottom,
  instead of being discovered at line 900.

Either answer takes an afternoon and makes the rewrite safe. Do not start the rewrite first.

## The work list behind it (observations Part 1, §2.15, Part 5)

**Five violations — concepts with no definition anywhere. Pure deletions:** `Frame.state`
(`discharged/exhausted/abandoned`, a bare Python string that refraction now keys its scope off),
`Step.state`, `_bookkeeping`'s 50-name set, `Rule.connective`'s Python copy (`conn(<R>, causes)` is
already reified and the engine reads its own copy at `machine.py:3141,3176`), `RuleSet.composed_from`.

**Ungated tier-3 concepts, one definition and one gate each:** `at_or_after` (three span cases —
start here, it is smallest), `scope_of`, `_recall`, `_would_change`, `discharge`, `_forbid`,
`_priority`, refraction. Three worked gates exist to copy: `ugm.state`, `ugm.arbitration`,
`ugm.agreement`.

## What was built today (uncommitted: chain, machine, rules, selftest, vocabulary, observations)

- **Refraction**, at the author's direction. An instantiation — rule plus **consumed entries plus
  bindings** — fires once. `spent(<R>, premises(...))` is deposited so the agent can be asked what it
  has already run. Frame-scoped, so supposing does not change what the agent believes. Measured: a
  runaway of 194 acts became 1; the starvation control now reaches quiescence and the referee gets
  its turn.
- **`contested(<R>, <what>)`** — the price of refraction, paid rather than accepted. Firing once turns
  a loud contradiction into a silent one, so when a spent instantiation's conclusion is denied **while
  its premises still stand**, that is deposited instead of looped.
- **`licensed_by`, `arrived_on`, `mentioned`** — §5 called licence and source "ordinary facts about
  the entry" while keeping them in Python. Now skeleton relations a rule can match. `Moment.licence`
  deleted: assigned once, read nowhere, while §4 claimed it was what said whether a moment was time or
  derivation.
- **A cached application can now be retracted.** `_applications` step 0 already dropped the cursor of
  a rule whose structural relation had grown — and it was useless, because step 2's merge is add-only,
  so **a full re-match could only ADD**. A negated structural member is evaluated at match time, so a
  stale application survived and applied. 537 checks passed with it live.
- **`_stored`'s anchor test** asked `is_var` where it meant *ground*. `loaded(?p)` counted as an
  anchor, so any corpus writing `rests_on(?e, foo(?p))` got a silent full-history scan.
- **`_vars_in` did not look at a relation**, while `Graph.has_var` always has. That is what blocked a
  **generic interpreter**: `ev_at(?verb(?a, ?b), ?t)` was refused at the surface while `match` handled
  it perfectly. Fixed, and one fixture moved with it — an unbound consequent *relation* is now refused
  at load like an unbound argument.
- **`ugm/necessity.py`** — a kill-probe over reserved names, the same shape as `ugm.bundle`.
  Suppresses each name's deposits and runs the suite. Four names nothing can kill: `computes`,
  `harmed`, `helped`, `stopped`. Building it found two instrument bugs, both caught by a null control.
- **A mirror gate** in the suite: every `Entry`, `Moment` and `Span` field is held to its graph
  counterpart, so the classes cannot silently stop being caches.

## Findings worth not rediscovering

- **Every defect this session found is a silence defect, not a correctness one.** The design's real
  standard is not correctness — it is: the agent can say what it means, a guess is on the record, and
  giving up deposits a fact. Heuristic and fallible is fine; silent is not.
- **The aggregate is the one real gap**, reached by four independent routes: *nothing was told about
  this*, *held at every moment of this stretch*, *exactly one thing satisfies this description*,
  *nothing has handled this yet*. All are claims about the **set** of matches. `root`/`blocked` are
  the shipped precedent — *an aggregate over what the rules produced is the machinery's business*.
- **But one-shot execution does not need it.** The locus does: place the grant at the moment the need
  sits at, spend it at the current one, and the denial outranks the re-grant while quiescence holds.
  Measured, no engine change. Three corpora had hand-built substitutes for this (`may(x, r)`, a round
  counter), which is business rules compensating for short-term amnesia.
- **`causes` and `implies` are identical with respect to re-firing** — 100 grants, 99 spends, both.
  The connective says where a conclusion lands, not that anything happens once. The design has no
  notion of a rule firing once; refraction is that notion.
- **A general interpreter is buildable and was built.** Generic over predicates, no lexicon — measured
  across two different commands with zero new rules. A new predicate costs nothing, a new grammatical
  role or syntactic form costs one row. The one thing it cannot do is definite reference.
- **The flood-fill idea has no motivating problem**: three real corpora, 39 own relations, **zero**
  morphological pairs. `attack`/`hits` are connected by a rule. The corpus's rules ARE the web.
- **The reserved vocabulary is the engine, not the bundle** — roughly two thirds is written or read by
  the machinery. But 42 of those names are **occasions**, and nothing gated whether they are
  load-bearing, which is what `ugm.necessity` now measures.

## Style

The author asked that star and warning markers never be used. 1,152 were removed from `docs/` and
`CLAUDE.md`; about 500 remain in Python docstrings and comments across 26 modules, and in
`MEMORY.md`. Do not reintroduce them.

---

# Handoff — 2026-08-14 (spans)

Branch `restart`. **520 checks, 0 failing**; every instrument green — `ugm.dungeon` 17/0,
`ugm.arbitration` and `ugm.state` 0 disagreements, `ugm.agreement` 28/0 with 7/7 exercised,
`ugm.backward` 7/0/0 blind, `ugm.shapes` 10 probes 0 changed, `ugm.workload` 25/0, `ugm.bundle`
**17 rules 17 exercised, 8 answerers 0 anomalies**, `ugm.compose` **9 checks** (was 7).

Two items. The handoff's item 1, **spans as loci** — and with it §13's *taking turns*, this design
document's own worked example of a shape, **which had never once run**. And then **`unless`, struck
off §22 without a line of engine written**, because it was a name for something already built.

## What the open class buys — measured, after the user named it

The user's observation: *working with an open class beats traditional programming because you do not
have to implement the meaning of everything — `owning`, `selling`. You create valid propositions and
give them a specific meaning later.* `ugm.vocabulary` is what turns that into a number instead of
agreement, and both halves hold.

**What the engine reserves, by what it serves** — 101 names:

| the agent's own deliberation | rules as data | the chain | the seam to a world | the surface | literals | **about any world** |
|---|---|---|---|---|---|---|
| 48 | 14 | 10 | 12 | 7 | 10 | **0** |

**Not one reserved name is a domain word.** No engine name for a thing, a place, an amount, or
an act of any particular kind — `did` and `says` are about the *act*, never its content. A corpus is
not writing inside someone else's ontology, which is the strong form of the claim and the thing that
would quietly be false if the floor had grown a world model.

**What a corpus borrows**, with the bundle as the control:

| corpus | about | its own | borrowed |
|---|---|---|---|
| a D&D fight | a world | 23 | 5 |
| **passenger rights on a disrupted flight** (new, `ugm/rules/delay.ugm`) | a world | 13 | **1** — `implies`, a connective |
| the design's worked examples | a world | 8 | 4 |
| **the bundle** | **the agent** | **0** | **25** |

**One classification, two opposite predictions, both hold.** The bundle borrows everything because
it is the one corpus about the agent's own reasoning. My first version of that check called the
bundle a **failure** — a check that fires on the case proving the classification right is measuring
the wrong thing, so the prediction is now signed by what a corpus is *about*.

**The price is the same property**: the engine cannot distinguish a proposition awaiting its
meaning from a **mistake**. Both well formed, both inert, nothing says which. A typo (`watns` for
`wants`) loads without complaint; `pred` meant the wrong thing; `plus`/`minus` were reserved
silently; and `unless` survived in three documents. Conventional languages front-load that into a
compile error, this back-loads it into silence — the right trade at session size and the wrong one at
Cyc's, which is why §20 puts acquisition first.

**And the property is not this design's invention** — it is the logic-programming and KR position
(Prolog, Datalog, RDF, Cyc). What is claimed is the discipline around it. Documented in §2, after
*closed is a rate, not a kind*, which it is the mirror of.

### `ugm.atlas` — a map of a corpus, and THREE independent defect classes

The user's follow-up: *a way to test the rules / corpus, e.g. build a map of the web or of the possible
inferential chains, and show it — maybe offline, with harmonization.* Then, sharpening the criterion:
*meaning means connected to the web; a rule mentioning a proposition alone forms a disconnected
subgraph. I expect islands (a domain's terminology) joined by bridges (common terminology), not a
densely connected web.*

`python -m ugm.atlas <corpus.ugm> [--mermaid]`. Three checks, and **none of them catches what the
others do** — which is the argument for having all three:

| | catches | what the others miss |
|---|---|---|
| a name nothing writes | `+bokked(?p, ?f)` | — |
| **the reachability fixpoint** | a rule whose premise is written *only by a rule that itself can never apply* | `unwebbed` cannot: the name **is** written |
| **connectivity** | a relation joined only to itself | it is written **and** grounded, so neither of the others looks at it |

**And it catches `authoring.md` §1's most expensive trap statically**: `-gone(?x)` where nothing
ever writes `gone` is a rule that can never apply, and that trap's whole cost is that it fails
silently.

**The prediction about the shape was made before the measurement and holds:**

| | relations | links | density | islands |
|---|---|---|---|---|
| passenger rights | 13 | 13 | 0.167 | [13] |
| the worked examples | 8 | 7 | 0.250 | **[4, 4]** |
| **two domains + the bundle** | 43 | 37 | **0.041** | **[1,2,2,3,3,4,5,10,13]** |

Sparse and fragmented, not a mesh. And the bridging terms divide exactly as predicted — each domain's
own hubs (`disrupted`, `owed`, `amount`; `likely`) alongside the agent's **common** vocabulary
(`says`, `did`, `goal`, `subgoal`, `verdict`). `worked.ugm` reporting **two** islands is the measure
being right about something known independently: that file is two unrelated worked examples.

**`not` reports as joined to nothing and is a false positive** — the bare variable distorting a
measurement for the **third** time. `<denial>` concludes `-?p`, which has no relation to draw a link
to, so `not` looks isolated while it is joined to everything the agent can deny. Excluded by name and
recorded rather than hidden.

**The conflict half is a prompt, not a defect list**, and the rate says why: **1** pair on passenger
rights (`weather vs crewing` — a flight both storm-delayed and short of crew has two answers and
nobody said which) against **28** on the dungeon, where they are almost all the ordinary
grant-and-spend cycle of a world model. **A corpus that CHANGES the world trips this far more than one
that concludes about it** — the shape census's gap, seen from the conflict side.

Static and argument-blind: `owns(smith, sword)` grounds `owns` for any rule reading `owns(?a, ?b)`.
So a rule it calls live may still never fire; a rule it calls **dead genuinely cannot**. The false
direction is the safe one.

### ...and the same property detects the mistake it enables

The user's follow-up: *could we detect vocabulary connected to nothing else? Meaning in the open class
is given by the web, and a vocabulary connected to nothing is for sure a mistake.* It is, and it
follows from the paragraph above rather than being a spelling heuristic.

**Only one direction is a signal, and measuring is what said which** — `harmony`'s lesson applied
before building, not after:

| | four healthy corpora | a corpus with a typo |
|---|---|---|
| written, never read | **11–17** — bookkeeping, plus a corpus's own *outputs* | fires, but buried |
| **read, never written** | **0, 0, 0, 0** | **1, and it is the bug** |

One direction suffices because **a typo always breaks a pairing, and a broken pairing always leaves
some reader with no writer** — so it is caught whether the misspelling lands in the rule or the fact.
Gated in `ugm.vocabulary` (18 checks), with a **planted typo carried as a control**, because every
real corpus reports zero and that is the same output a detector that had stopped working would give.
Three kill-probes: a typo in a real corpus (3), the reserved-name exclusion removed (1), the control
quietly fixed (1).

**Known false positive, stated now rather than discovered later:** a corpus fed by a live channel
legitimately reads names its own text never writes. All four corpora here assert their world in the
file.

**And a new instrument trap, caused by my own kill-probe.** After probing the control by swapping
`watns` for `wants` and restoring, the detector reported all-clear on the control and stayed that way.
The file on disk was correct; **Python was reusing a stale `.pyc`**, because the two spellings are the
same length, so the restored file had an identical size and an mtime in the same second. A probe whose
edit is byte-length-identical can leave its own result behind and make it look permanent — and the
symptom is a detector that has quietly stopped detecting, which is the exact failure the control
exists to catch. `rm -rf ugm/__pycache__` after a restore, or vary the length.

**Open, and the natural next question:** whether this should run at **load** and warn the author,
the way `plus`/`minus` shadowing now does. It is an instrument today, so nothing tells an author
until someone runs it.

`delay.ugm` is **run and asserted**, not merely counted: a corpus a census only parses is
decoration, and would let the census report a vocabulary for rules that do not work.

## `unless` was a NAME, not a gap — and the user's question is what found it

The user asked, of a scoring table I had just produced: *I really don't understand why expressing
"unless" is so complicated. It makes me think it's caused by something else that is wrong.* Then:
**`unless` is "if not".**

It is, and *if not* has been in the surface since there were members:

```
rule <regen> = implies( { +wounded(?x), -poisoned(?x) }, { +heals(?x) } )
```

| | |
|---|---|
| `heals(ally)` — not poisoned | **`+`** |
| `heals(hero)` — poisoned | **`None`**, blocked |

That is the **per-entity exception** `authoring.md` §2 says precedence cannot express — `overrides` is
per rule and per tick, `supersedes` needs a shared consumed entry, and a guard needs neither. And R3,
the one thing writing it as a separate *fact* would have bought, is already served: `reify` deposits
every member with its sign, so *what would cancel this rule* is a query over
`ant(<regen>, poisoned(?x), -, 1)`.

**Everything that made it look hard came from writing the guard somewhere ELSE.** §8 scopes a
rule's variables to its own statement, so `fact unless(<regen>, poisoned(?x))` parses, is read by
nothing, and its `?x` is a *different node* — measured, **757 against 729**. That is the `excluded`
wall, which has now blocked `adopt` and `generalise` too, and it was never `unless`'s problem.

**What that struck, in four places:** §22's open item, Appendix C's table, `RuleSet.compose`'s
docstring, and — worst — `docs/authoring.md`, where **this session's own earlier commit** had just
rewritten the table to call `unless` "the only unbuilt row". I took that from the design doc instead
of testing it, which is the exact habit this repo keeps catching.

**And guard inheritance in composition turned out to be COMPLETE**, which `compose` had been
apologising for in a docstring and `ugm.compose` had been *printing* as a finding without ever
testing it. A guard is an ordinary antecedent member and composition takes the union of the
antecedents, so it is inherited by **construction**. Verified from either constituent, and as
behaviour rather than structure — a member carried and not obeyed is `adopt`'s own defect.
`ugm.compose` is 9 checks where it was 7, and the apology is now two of them.

>**An instrument that PRINTS a limitation it never tested is the same defect as a check that
>cannot fail** — and this one had been printing it since composition was built.

**What is genuinely absent, correctly named: amendment at a distance** — adding a guard to a rule
you did not write. **Decided, not deferred:** an ordinary rule may not reach into another rule's
application, which is §5's wall, and amending a rule belongs to **harmonization** — the agent authors
a better rule through `adopt`, so the amendment is itself a claim that can be dated, attributed and
argued with, rather than a patch applied by something that was only supposed to be reasoning.

## The session in one page

>§11, for as long as it has existed: **DESCRIBED AND NOT IMPLEMENTED.**
>§13, underneath its two worked rules: **NEITHER OF THOSE TWO RULES CAN BE WRITTEN IN ANY CORPUS
>THIS ENGINE LOADS.**

Both boxes are gone. A span is a node with two members, `span_of(?s, ?start, ?end)` mints or
decomposes one, an entry's locus may be either, and §13's `<TT-base>`/`<TT-step>` recognise *taking
turns* over **every stretch it holds over** — ten of them across five moments, argument swap correct.

**And the wall was not where §11 put it.** The section lists three costs — normalisation, the
quadratic population, the ancestry check — and all three together were an afternoon. What actually
stood between the page and a running example was **three lines that read a locus and ignored it**,
none of which §11 mentions, because each was correct exactly while every locus was a moment:

| where | what it did | kill-probe |
|---|---|---|
| the **write** | a consequent's `at ?m` was parsed, boundness-checked and reified — and the gate stamped the frame's topic anyway | 4 |
| **quiescence** | asked whether the conclusion already held at the frame's *topic*, so a second recognition of one proposition was *nothing to do* however different the stretch | 3 |
| the **resolved state's key** | one entry per proposition — an assumption about **loci**, not about propositions | 1 |

**The first two are one defect twice, and fixing the write alone bought nothing** — the loop never
reached the write, because the verdict was computed about a different locus than the one the
conclusion would land at. This is *a knob read and not obeyed* (`adopt`'s finding about a rule's
grade) arriving at the locus, and it was invisible because two entries differing only in their locus
look identical to every outcome check in the suite.

**Measured cost of the whole change: nothing.** The unmodified 506-check suite runs on the new engine
in **8.7s against 8.7s**, and passes.

## The four decisions, each scored before it was taken

1. **Inheritance is within a kind of locus.** A moment asking about a span-located claim gets
   it once the stretch is **over** — without that a shape's conclusion is visible to nothing. A span
   asking about a moment-located claim gets **nothing**: *it rained at M9* must not answer *did it
   rain throughout M7..M12*, because the read returns one winner rather than scanning an interval, so
   **a denial in the middle of the stretch would be invisible**. Free, unarguable, and wrong only
   sometimes is the worst combination this design knows. A corpus that wants the entailment writes
   the rule, and then it is dated and deniable — §12's grade deletion, made again.
2. **`span_of`, a member, not notation.** `entry_of`'s shape one construct along: endpoints bound
   ⟹ mint (which is what §11 means by *minted by recognisers*), span bound ⟹ decompose, unanchored
   ⟹ nothing, because any two moments form a span.
3. **The ancestry check twice, at its own site each time.** The matcher's member *finds nothing* —
   the engine's uniform answer to a pattern nothing satisfies — and `Chain.span` *raises*, because a
   machinery reaching there with an inverted pair has made a mistake that is still attributable.
   A **degenerate** span is refused with it: `span(M7, M7)` is a second name for a moment.
4. **The state is keyed by proposition AND span.** Supersession needs comparable loci; two spans
   are not comparable, so each is its own key space.

## A shape is three rules, and the split is §6's own

§13's example needs the **raw chain**, and §12 said so in advance: an alternation repeats its actors,
so `acts(anna)` at M1 is superseded by `acts(anna)` at M3, and *a single fact's own history is not
relatable* through the resolved state. §12 names the remedy in the same breath — *matching over the
raw chain, which is what §6's stratum-0 read is for* — and since `merged` that is one interpreter.

So the two recognisers mention only structure and therefore **conclude structure** (§6's test), and
one ordinary rule says it:

```
rule <say> = implies( { turns(?s, ?a, ?b), +watching(x) },
                     { +taking_turns(?a, ?b) at ?s } )
```

**One to see it, one to say it** — `reached`'s finding, arrived at independently from the shape
side. The claim deposited is an ordinary entry at a span locus: dated, attributed, deniable, and
readable by any rule from the end of the stretch onward.

## What the instruments caught that I would not have

* **Without interning, the recursion never terminates.** The kill-probe minting a fresh node per
  span is the only one that does not fail — it **runs away**, no answer in 300s. The twin trap's cost,
  for once, as a hang rather than as a silent wrong answer.
* **My own prose claimed more than the probe supported.** I wrote that the state key is what lets
  §13's recursion see its own output; it is not, because that recursion is in the structural layer,
  which never consults the resolved state. Removing the key breaks exactly **one** check — the one
  asserting it directly. Corrected in `chain.scope_of` and in §11, both of which had already been
  written up as the stronger claim. *Measure before writing down that you did*, from `seminaive`,
  holding for a second session running.
* **Two of my probes were twins, and neither engine bug existed.** `g.atom` mints, so a fixture
  building `acts(anna)` beside the corpus's table matched nothing and looked exactly like a broken
  matcher. Twice, minutes apart. The fixtures go through `kb.term`.

## The debt this leaves

* **`at_or_after` now answers two different questions with one function.** For `resolve` it means
  *does this claim answer my question*; for `practice._charge` and the containment checks it means
  *is this locus within my reach*. Those agree for moments and **come apart for spans**:
  `Span.at_or_after(moment)` is `False`, which is right for inheritance and wrong for containment —
  a span starting after a frame's origin *is* the frame's own doing. No live path reaches it (the
  callers are moment-only today) and nothing would catch it if one did.
* **`settle_structure` is still not called by the tick loop**, and spans make that sharper rather
  than answering it: a shape recogniser only runs when something calls `ask_read` and settles the
  structural layer. A corpus author has to know that, and `docs/authoring.md` now says so.
* **Span containment is unread** — a claim over M7..M12 does not answer about M9..M11. That is
  deliberate (an interval relation is an ordinary fact about endpoints), but no corpus has written
  `during` yet, so the claim that it is *expressible* rather than merely *permitted* is unexercised.
* **Still absent**: `where` as a keyword and §12's `?t = entry(...)` prefix form, both cosmetic now
  that the member forms exist. `unless` is **struck** — see the top of this handoff — so
  `docs/authoring.md`'s unbuilt table now has **no rows left**.
* **The `excluded` wall is the real open question**, and it has now blocked three features while
  wearing three different names (`adopt`'s composer, `generalise`'s trail examples, `unless`'s
  guard). §8 scopes a statement's variables to it, deliberately and load-bearingly. Nothing here
  argues it should change — but it is worth naming once, because each time it is met it looks like a
  new limitation of whatever feature met it.
* Unchanged and untouched: the dungeon's *did it keep deriving after its verdict* instrument, and
  **no foreign corpus has authored a goal**, which remains the biggest unknown on the list.

## Where I would pick up

1. **Get a foreign corpus to author a GOAL.** Now the largest unknown by some distance — backward
   reading has never been exercised from outside this repo, and every other item on this list is
   smaller than it.
2. **Examples from the agent's own trail**, still unblocked and still not done: `rests_on` is a
   member, so anti-unification can read the agent's own derivations. Open since `generalise`.
3. **Decide whether the tick loop settles structure.** A design question, and shapes are the first
   thing that makes an author trip over the answer.
4. **Amendment through harmonization** — now the correctly-named version of what `unless` was
   standing in for, and decided in principle: the agent authors a better rule through `adopt` rather
   than patching one in place.

**The habit held again, and from the other side.** §11 had a costs section listing three things,
and none of them was the problem; the problem was in three files §11 does not mention. **A section
that lists its own costs is not the same as a section that knows what it costs** — and the way to
tell is to run its worked example.

# Superseded: 2026-08-14 (later)

Branch `restart`. **506 checks, 0 failing**; every instrument green, `ugm.dungeon` 17/0,
`ugm.bundle` 17/17 and 8 answerers with 0 anomalies, `ugm.arbitration` 0 disagreements.

Three commits. `merged` is the handoff's item 1 — **the matchers are one, and `stratum0.py` is
deleted**, 306 lines out, the read written as ordinary rules in the surface a corpus writes. `reached`
is what it took to make that capability **reachable by a corpus**, which turned out to be three
separate defects and a fourth that was a genuine soundness bug. `seminaive` made the merged read
**34× faster**, and the larger half of that was somewhere nobody was looking.

## `seminaive`: 14.4s → 0.42s, and only a third of it was the planned change

The last handoff named semi-naive evaluation as the one thing between the merged read and being
usable outside the gate. It was the right change and it was **not most of the cost.**

| | |
|---|---|
| naive fixpoint | 14.4s |
| **semi-naive** — a rule re-runs only when a relation it READS has grown | **5.6s** |
| **`has_var` decided at mint** instead of walked per question | **0.42s** |

**Profiling said `has_var` was 91% of what remained** — 7.6M calls, re-walking a whole structure
each time, because the structural generators ask it of every instance in a bucket on every
enumeration. A node's relation and members are fixed when it is built, so its genericity is fixed with
them; deciding it once is O(arity) at mint instead of O(size) per question. **The gate went from about
two minutes to 2.9 seconds**, and the whole suite benefits, because every matcher asks this.

**And one optimisation I made bought nothing, which is the same lesson from the other side.** I
removed the list copy in `instances_of` for the structural generators on the reasoning that a
193-element bucket enumerated 193 times must be the cost. Measured: **5.58s → 5.68s**, i.e. noise. It
is reverted, and it had already been written up in a docstring as a measured win before it was
measured. *Measure before optimising* — including before writing down that you did.

The semi-naive rule is one sentence: **a rule's matches depend on exactly the relations in its
antecedent**, so if none of them grew, it can produce nothing new. It pays where the layer is uneven,
and the read's is — `cand` is the expensive rule and reads nothing derived, so it runs once instead of
once per pass. It is the **coarse** form, by relation rather than by fact; true semi-naive would
hand each rule only what appeared, and cannot reuse `match`'s `fresh` because that is a `Situation` of
entries and these are not entries.

**The cached genericity is an index over what it re-implements**, so the walked definition is kept
as `Graph._has_var_slow` and a check holds the two to each other over every node three loaded machines
build. `state` paid for that lesson once already.

## What the second commit found, and it is the more useful half

The merge worked and **no corpus could use it.** Writing the obvious next thing — *the door was open
and now is closed*, which §22 recorded as *not sized, materially harder* — turned up three engine
defects between the capability and an author, none of which any outcome check could see:

| defect | how it showed |
|---|---|
| `asking` was seeded **only by the gate** | every structural member is anchored, so a corpus's chain rules matched **nothing**, silently |
| quiescence asked `resolve` about a conclusion that never enters the chain | the rule **never stopped** — 60 ticks of `applied`, identical bindings |
| a structural fact enters **no delta** | incremental matching **never re-triggered** the rule that reads it, so it fired once, before the fact existed |

**And the fourth was the interning trap, for the fourth time in two commits — this one a
soundness bug rather than bookkeeping.** `substitute` interns, so a quiescence verdict computed with
it **makes the conclusion exist**, and whoever asks next is told there is nothing to do. For an
ordinary conclusion that is harmless; for a stratum-0 one the node's existence *is* the fact.

>**Asking whether a stratum-0 rule would change anything made it not change anything.**

`ugm.arbitration` caught it — the fast path chose a move the slow path then found nothing for, because
**one path's question consumed the other's answer**. `rules.already_there` is the same walk with no
minting in it, and it needs **three** answers, not two: *generic*, *ground and absent*, *already
there*. Collapsing the first two sends the caller back to `substitute` to tell them apart, which is
the mint it exists to avoid.

**The interning trap's four faces, all in this arc**, because the pattern is worth naming: the
fixpoint's novelty test **never fired** (right facts, no fixpoint); quiescence's existence check
**always fired** (the rule never started); the delta invalidation **recorded nothing** (quiescence had
already interned it); and the verdict **was not pure** (two paths disagreed). Same cause, four
opposite symptoms.

**What a corpus can now write**, verified end to end and in `docs/authoring.md`:

```
rule <flip> = implies(
  { asking(?s), anc(?s, ?d1), in_delta(?d1, ?e1), entry_of(?e1, ?l1, ?p, plus),
    anc(?s, ?d2), in_delta(?d2, ?e2), entry_of(?e2, ?l2, ?p, minus),
    sanc(?l2, ?l1) },
  { flipped(?p) } )

rule <note> = implies( { flipped(?p), +watching(x) }, { +changed(?p) } )
```

**A rule may read the raw chain precisely because it cannot assert anything about what it
finds.** `<flip>` mentions only skeleton, so §6's test makes its conclusion structure — undated,
unattributed, not deniable. `<note>` mentions an entry, so it is ordinary and concludes a claim. One
to see it, one to say it, and the bootstrap stays closed.

## The session in one page

The task was *resume from the handoff*, whose item 1 said feasibility was established. **It was
established for the antecedent and silent about the consequent, which is where the wall actually is.**

>§6: *Stratum 0 must produce structure, not entries. If the walk deposited its intermediate results
>as claims, it would be reading entries and the circle would return.*

An ordinary rule concludes an **entry**, deposited through the gate into a state that the read
produces. So porting `cand`/`beaten`/`best` to ordinary rules as they stood would have reinstated §6's
bootstrap circle. The way through was not a new construct but **§6's own sentence made operational**:

>§6 defines stratum 0 as *a property of a rule* — every antecedent member is structural — decided *by
>inspecting an antecedent rather than by a designer assigning layers.*

That test is computable, so it is computed, and it decides **both halves at once**: a rule that reads
only structure is applied without a read, and therefore concludes into the skeleton rather than the
chain. No rule subtype, no marker on the surface, no second interpreter. §5's *one interpreter* and
§6's *one more row, not one more branch* are now true of the code and not only of the intent.

| what | how |
|---|---|
| the skeleton as members | `anc`, `in_delta`, `delta_next`, `rests_on`, `entry_of`, `asking` |
| where a conclusion lands | `RuleSet.is_stratum0` — §6's test, over a fixpoint from below |
| the layers | `RuleSet.strata` — SCCs of the dependency graph, **derived, not assigned** |
| negation | a `-` on a structural member. **No notation was added** |
| the read | 7 ordinary rules in `ugm.agreement`, 28/28 agreeing, 7/7 killable |

**Four things worth keeping.**

1. **Negation needed no syntax, and `unless` was never the blocker.** I assumed item 1 was
   blocked on `unless` (§22 lists it absent). It is not: `unless` is defeasibility *over rules*; the
   read needs a **negated member**, which is a different thing. And on a structural member there is no
   entry for a sign to be a claim about — so `-beaten(...)` can only mean *not derived*, and
   `text.py` already parsed it. `unless` remains absent and remains a separate item.
2. **The anchoring discipline divides where I first drew it wrong.** `_stored` refuses an
   unbound pattern because the chain's relations are facts about the **whole history**. But a relation
   a stratum-0 rule *derived* exists only because something asked, so requiring an anchor there
   refuses the read its own conclusions — and did: `cand` derived 193 while `beaten` and `best`
   derived **nothing at all**. Two functions, `_stored` and `_bounded`, and the line between them is
   *is this a fact about the history, or a consequence of the question?*
3. **The fixpoint counted novelty after the thing had been created.** `substitute` builds the
   grounded node with `g.rel`, which interns — so the fact was minted *there*, and the novelty test
   made afterwards always found it present. Every fact derived correctly and the loop believed it had
   derived nothing: one pass per layer, no fixpoint, and a read answering from a third of its
   candidates. **It failed as a wrong answer rather than as a crash**, and only the agreement gate
   caught it.
4. **Two of my own checks could not fail, both recorded traps.** The stratum-0 conclusion check
   drove `settle_structure`, which calls `_mint_structure` directly and never reaches the branch in
   `_conclude` it was written to test — the kill-probe broke **zero** checks. And *nothing new on the
   second run* is satisfied trivially by a novelty test that never fires, so it could not see the very
   bug above; what discriminates is a transitive closure **five deep**, which needs the layer re-run.

### A live defect found on the way, in a name nobody had written

**`pred` was the reflexive-transitive walk under the name of the immediate one.** It was
registered for corpora (`machine.py`'s name table) and written by no rule in this repo or the foreign
one, so nothing could see that `pred(?m, ?n)` yielded every ancestor *and* `?m` itself. `anc` is that
walk and now carries the name; `pred` is the stored fact the chain actually deposits. **A name a
corpus may write whose meaning is not what the name says is worse than an absent one**, because a
corpus that used it would have been right to trust it.

### What this closes, beyond item 1

* **§22's *whether an ordinary rule may read the skeleton*** — *"neither is obviously right and the
  question is not small"*. It is answered: **yes, and without promoting anything to entries**, because
  the reading rule concludes structure too. That also unblocks **examples from the agent's own trail**
  (`rests_on` is now a member an ordinary rule may write), which has been open since `generalise`.
* **§6's *one interpreter*** and **§5's wall**, both previously false of the code.

### The debt, in one place

* **The read's speed is no longer the blocker** — 0.42s on the five-moment fixture, gate 2.9s. What
  remains is the **coarse-to-true** refinement of semi-naive (by fact rather than by relation), and
  nobody has needed it. `settle_structure` is still not called by the tick loop, and whether it should
  be is now a design question rather than a performance one.
* **Containment is now compositional rather than structural for `_stored` members.** `_anchored`
  cannot reach a sibling *whatever* is bound (§11: one parent, several successors); `_stored` cannot
  reach one *given how you got here*. The fork check holds it, and it is a **measurement now, not a
  construction**. The argument rests on the seed: `Machine.ask_read` is the only caller, and a
  machinery seeding a seat the frame cannot see would derive about it with nothing structural
  objecting.
* **`ugm.agreement`'s read is a corpus, so it is not the bundle's.** Nothing ships the read as rules;
  the gate loads them. Whether the bundle should carry them is undecided and is the same question the
  collapse table has been sitting in since `ungraded`.
* **Still absent, unchanged**: `unless`, `where` as a keyword, §12's `?t = entry(...)` **prefix** form
  (the *member* form now exists as `entry_of`), and **spans as loci** — so §13's shapes remain
  unwritable. **The span is now the only representational gap left in the skeleton**, which is a
  smaller and sharper statement than this list has been able to make before.
* **Structural invalidation is blunt, by relation and unconditional.** A derived skeleton fact
  drops the cursor of every rule mentioning that relation, so those rules are matched in full again.
  It over-invalidates — the alternative under-invalidates and loses the conclusion permanently — and
  it is recorded rather than measured. Nobody has priced it on a corpus that leans on the skeleton.
* **The dungeon's two open items**, still untouched: the *did it keep deriving after its verdict*
  instrument, and **no foreign corpus has authored a goal**, so backward reading is still unexercised
  from outside.

## Where I would pick up

1. **Spans as loci.** Now the **only** representational gap left in the skeleton, and the one that
   keeps §13's shapes — *taking turns*, the design document's own worked example — from ever having
   run. `Entry.locus` is typed as a moment; until it is not, §11 describes a construct the engine does
   not build. It touches `deposit`, `resolve`, the gate and `entry_of`, so it is the session-opening
   kind of task, not the session-closing kind.
2. **Examples from the agent's own trail**, newly unblocked: `rests_on` is a member now, so
   anti-unification can read the agent's own derivations instead of corpus facts. Smaller than spans
   and it closes an item open since `generalise`.
3. **Get a foreign corpus to author a GOAL.** Still the biggest unknown on the list, and unchanged by
   any of this — backward reading has never been exercised from outside this repo.
4. `where` as a keyword and §12's `?t = entry(...)` prefix form — cosmetic now that `entry_of` exists,
   and worth doing only alongside spans.

**The habit held.** Item 1 looked like it needed `unless` and a new consequent construct; it needed
neither. Both walls were **refusals nobody had argued for**, and the answer to each was a sentence
already in §6.

# Superseded: 2026-08-14

Branch `restart`, pushed. **491 checks, 0 failing**; every instrument green, including a **foreign
corpus** (`ugm.dungeon`, 17/0) that another session wrote and that now exercises everything below.

## The session in one page

Twenty-five commits, and the shape of them is the point. The task was *rewrite the design doc*. What
actually happened is that **writing the document down honestly turned four documented conventions into
to-do items in an afternoon**, and then a foreign corpus arrived and turned three more into features.

| commit | what it settled |
|---|---|
| `rederived` | the doc re-derived from §1, grades gone throughout, **§20 acquisition** added, §21/§22 renumbered |
| `unbuilt` | the **skeleton, spans and shapes are described and not implemented** — §13's worked example has never run |
| `rises` | §16's change-term: direction is a wrapping proposition beside `?`, and the definition mentions before/after |
| `shapes` | `ugm.shapes` — the census, the expressibility probes, the composition proof |
| `trigger` | composition gets a **corpus-side trigger**; `composed(<c>,<a>,<b>)` closes §1's defect for the 12th time |
| `boundary` | composing across a `causes` **loses conclusions** — refused, exactly |
| `authoring` | `docs/authoring.md`, every snippet verified against the engine |
| `unsayable` | the **four kinds** of unsayable — and two rows struck through the same day |
| `class` | a **variable in relation position**: `sells(smith, weapon)` names a class, `?kind(?item)` applies it |
| `magnitude` | a known amount is a **tool**; an unknown one is a **node** (§13's move for plurality, on a scalar) |
| `shadowed` | `plus`/`minus` were reserved and a corpus found out **silently** — now reported at load |
| `halfway` | a transfer mid-flight was observable **and actionable**: the agent emitted on twelve gold that never existed |
| `skeleton` | `+acts(goblin) at ?m` — a member says **where** its entry sits |
| `names` | `+on(?x,?y) as ?t` — a member names **what** it matched; the same node, not a copy |
| `computator` | values in, a value out, **never the graph** — purity is structural, and the transfer becomes atomic |
| `transit`/`unknown` | the atomicity item, corrected **three times**, ending in: `?` was always the vocabulary |
| `skeleton2` | the **skeleton is an ordinary member** — `sanc(?mq, ?mp)`, no request, no second matcher |
| `retired` | ...and the `order`/`precedes` answerer built that afternoon is **deleted** |

**Four shapes, each of which paid more than once.**

1. **A wall nobody had argued for.** `?p(?x)`, magnitude, and the skeleton's locus were all on
   the open-questions list as representational limits. Each was **three independent refusals with no
   argument behind any of them** — a parser that would not read it, a comparison by identity, a
   substitution that would not rebuild. Each took about an hour. **The information was already there
   and one line did not look at it**, four times.
2. **The user asked *why*, and the answer deleted the work.** Every correction this session came
   from a question rather than from building: *is it the engine or our rules?* · *doesn't a genuinely
   slow change really have an intermediate?* · *isn't structure graph like anything else?* · *are we
   enforcing policy on the open class?* Two features were **deleted** and one open item **closed**
   as a result.
3. **My checks passed for the wrong reason, three times.** A containment check that read
   containment's own silence as a refusal; an ancestry check whose discriminating case was
   unreachable; a downward-walk check anchored where nothing descended. **A check about what cannot
   be reached needs a fixture where there is something to reach.**
4. **The twin trap, twice more, by the author of the note warning about it.** `self.BINDS`
   collided with plan bindings (every plan printed `names(...)`); a computator built its result with
   `g.atom`, so `twice(4, 8)` landed under a **twin** `8` and every question about it answered
   nothing. Both found by instruments in under a minute; neither by reading.

### What a foreign corpus bought, and it is the headline

Another session wrote `ugm/rules/dungeon.ugm` — 21 rules, a D&D combat round — and answered
`docs/authoring.md` §8 with `docs/dungeon-feedback.md`. **Every number in it reproduced exactly.** It
found a live bug we could not have found (`plus`/`minus`), predicted a soundness hole we then
constructed (atomicity), and **corrected the shape census**:

| | internal | dungeon |
|---|---|---|
| the two primitives cover | **73.9%** | **28.6%** |
| rules retracting in their own consequent | **1 of 17 bundled — 6%** | **12 of 21 — 57%** |

**The bundle was derived from an agent that CONCLUDES; a world model CHANGES.** That is the
whole gap in one number, and it explains why arithmetic, ordering, comparison and joint update were
all absent *consistently* — none is needed to reason and all are needed to simulate.

And it answered §6's sizing question precisely: they needed **sequencing only, never a fact's own
history**, and **24% of their corpus was clock scaffold** re-implementing a moment ordinal. That is
what justified building `at`, `sanc` and the rest.

### The debt, in one place

* **`stratum0.py` is still a second matcher**, which §5's *one interpreter* forbids and §6
  explicitly disclaims. **Feasibility is established**: an entry is an ordinary relation instance
  (`entry(moment(), on(a,b), +)`), and the read's own rules are all **anchored** — up from the seat,
  then bounded enumeration. So the read is expressible under the anchoring discipline.
  It rewrites *the bundle's central program*, and `ugm.agreement` uses `stratum0` as the **baseline**
  it measures the native read against — so the gate's comparison has to be rebuilt with it. **Start
  this fresh, not at the end of a session.**
* **Still absent**: `where` as a keyword, §12's `?t = entry(...)` prefix form, **spans as loci** (so
  §13's shapes remain unwritable), and `unless`.
* **The dungeon's two open items**, neither touched: an instrument for *did the agent keep deriving
  after its verdict, and how much* (they saw a correctly-decided fight run to round 417 with every
  outcome check green); and — the one that flatters every number above — **zero goals were authored**
  in their corpus, so **backward reading has never been exercised by a foreign one**.
* **A transitional state has no marker, and should not get one.** Corrected three times: the artifact
  half is fixed by computators; the real half is *true* and should be visible; and saying it needs
  nothing new, because `?` already means *I do not know this yet*. What has no enforcement is an
  author remembering to write `?` instead of a number they cannot justify.
* **Composition's trigger is a corpus's**, deliberately (§21's judgement census). *Compose what has run
  often and never surprised* is still nobody's rule.
* The **judgement census** (§21) has three entries and one of them, `_in_play`, is still unargued.

## Verify in one go

```
python -m ugm.selftest      491 checks, 0 failing    the runner; any False is a failure
python -m ugm.dungeon        17 checks               a FOREIGN corpus -- a D&D combat round
python -m ugm.arbitration     0 disagreements        the move, fast against the slow definition
python -m ugm.state           0 disagreements        the kept state, against the walk
python -m ugm.agreement      28 reads, 12/12         the rule-level read against the native one
python -m ugm.bundle         17 rules, 8 answerers   is every shipped rule and answerer load-bearing?
python -m ugm.backward        7 checks, 0 blind      backward reading, as rules
python -m ugm.compose         7 checks               composition, and the `causes` boundary
python -m ugm.shapes         10 probes, 3 checks     what shapes rules have; what the surface expresses
python -m ugm.modality · workload · learning · tools · harmony
```

`ugm.bundle` takes several minutes -- it re-runs the whole suite per mutation. Background it.

## The state of the code

**27 modules.** `chain` `graph` `gate` `rules` `channels` `machine` `text` are the engine; `__main__`
is the door; `stratum0` is the rule-level read **and still a second matcher**; the rest are
instruments.

**What a rule may now write**, all new this session:

```
+acts(goblin) at ?m           WHERE the entry sits          -- a member's locus binds
+on(?x, ?y) as ?t             WHAT it matched, named        -- the same node, not a copy
sanc(?later, ?earlier)        the SKELETON, directly        -- anchored, upward, no answerer
minus(?x, ?n) as ?new         a COMPUTATOR                  -- values in, a value out, never the graph
+?kind(?item)                 a relation named by a variable -- a class as data
```

**Seventeen bundled rules**, **eight answerers** (four `standing`), **three doors** (`_adopt`,
`_dispatch`, `_enter`), **four guards, one move** (`_forbid`, `_widen`, `_recover`, `_notice_open`),
**two evaluated-member kinds** (computators, structural relations), **zero phases**.

**Registration doors**: `Loader.computator` and `Loader.answerer`. Both resolve names in the
CORPUS's scope, and both must -- a value or request minted beside the corpus's table is a twin the
corpus can never name. That trap fired twice this session.

## Where I would pick up

In order of how much they would buy, and the first is the only large one.

1. **Merge the matchers — the read as ordinary rules, then delete `stratum0.py`.** §5's *one
   interpreter* and §6's *one more row, not one more branch*, both currently false of the code.
   Feasibility is established (see the debt above). Rebuild `ugm.agreement`'s baseline as part of
   it, not after -- a gate whose comparison moves under it is worth nothing.
2. **`where` and §12's `?t = entry(...)`** -- smaller now that structural members exist, and it is
   what §13's shapes need after spans.
3. **Spans as loci.** `Entry.locus` is typed as a moment; until it is not, §11 describes a construct
   the engine does not build and §13's shapes cannot be written at all.
4. **The dungeon's instrument**: *did the agent keep deriving after its verdict, and how much.* Same
   family as §21's judgement census -- something no outcome check can see.
5. **Get a foreign corpus to author a GOAL.** Backward reading -- `fit`, `check`, `verdict`,
   `subgoal`, `blocked`, `<give-up>` -- has never been exercised by one. Half the apparatus is
   untested outside this repo, and that is the biggest unknown on this list.

**Standing hazards, none enforced.** *An occasion warrants a re-ask only if re-asking cannot produce
one* -- now violated in five separate places, four of them fixtures written this session. And a
corpus that asserts a value it cannot yet justify re-creates the atomicity hole with no help from
anything; `?` is the answer and nothing insists on it.

**A habit worth keeping.** Every correction this session came from being asked *why*, not from
building. Two features were deleted and one open item closed that way. When something reads as a wall,
the prior that earned its keep today is: **it is three refusals nobody argued for.**

# Superseded: 2026-08-13

Branch `restart`, pushed. **448 checks, 0 failing**; every instrument green.

## The session in one page

Nine commits. The first two were speed, the next four built **acquisition**, and the last three are
what happened when acquisition was made to meet **harmonization** — two of which are deletions the
meeting forced.

| commit | what it settled |
|---|---|
| `kept` | the loop went **linear** — index and keys maintained where the state is; 12,800 facts in less time than 1,600 took that morning |
| `join` | `pystrider` found a **second quadratic** — the join, not the option set. 2,006,004 unifications → **3,003** |
| `defeated` | `defeated(<loser>, <winner>)`, and `ugm.harmony`: **not one unplanned conflict in the repo**, so a detector could not be gated |
| `adopt` | **a rule can author a rule** — the reverse of `reify`, a door beside `_dispatch` and `_enter` |
| `generalise` | anti-unification, **the dual of `unify`**: two examples become a rule that fires on a third case |
| `ungraded` | **`@likely` deleted** — `weaker` was called from one place; the grade was carried, composed, printed and never obeyed |
| `precede` | the **composition test**, which broke in two places and found both |
| `authored` | precedence **read, not kept** — the table deleted at a measured cost of nothing |
| `wrapped` | the third precedence relation this all seemed to need **does not exist and should not** |

**Four shapes, each of which paid more than once.**

1. **The fix is a deletion, four times.** Grades, the precedence table, `Loader._maybe_precedence`,
   and — the best one — a relation that was never built, because measuring showed a wrapped conclusion
   cannot conflict at all.
2. **Measure before building, and the measurement keeps refuting the plan.** Harmonization's
   detector: unfalsifiable on these corpora. The grade: used by 4 of 3,740 rules. The third
   precedence: unnecessary. Every one of those was going to be built.
3. **Composition is where the bugs are.** `precede` existed only to make four commits meet, and it
   found both a §21-shaped defect (a rule says what the machinery ignores) and a twin (the adopted
   rule was not the rule the graph described). Neither was visible from inside its own commit.
4. **My instruments failed five times, all recorded traps.** `id()` reuse under-counted a census
   3.5×; a comparison instrument scored the suite's own deliberate mutants as disagreements; a check
   asked machine 2's key set about machine 1's node; a learner closed over the wrong machine's loader;
   a kill-probe crashed a check instead of failing it. The pattern is stable: **the instrument is
   where the mistake is.**

### The debt, in one place

* `docs/rules-design.md` has ~80 references to grades. §12's *where the grade lives* carries the
  re-run and the measurement; **the rest is now partly describing an engine that does not exist.**
  CLAUDE.md calls that file the only doc, so this is real and it grows with every commit.
* **The collapse table** for nested modalities (`{+likely(possible(?x))} ⟹ {+possible(?x)}`) is a
  corpus's to write and the bundle ships nothing. §19-correct, and the same shape as the `<recheck>`
  line now recorded three times as missing — worth deciding once whether the bundle carries this
  family.
* **`_in_play`** is the one judgement still in Python that `named` left half-open: the goal half could
  be facts, the delta half cannot on an append-only chain.
* **Loop detection** is still designed, measured and unbuilt — but no longer unfalsifiable: two
  fixtures now produce the pathology on demand (an `overrides` cycle, and a conflict that starves the
  rule that would settle it).
* **The named next slice:** retire a learned rule on the **credit walk** (`harmed` carries a count),
  not on `defeated`, which is deduped per pair and so can only say *once is enough* — measured wrong.
* Still open from earlier: the **use/mention wall** (an intent naming a rule cannot leave the agent,
  because a rule node is generic), and **examples from the agent's own trail** (blocked on `rests_on`
  being skeleton rather than entries).

## Latest: **what a learned rule may conclude** — and the vocabulary that looked missing is not. Commit `wrapped`.

Pushing the learning-and-harmonizing arc on its normal case: the agent generalises
`{+hinged(?x)} ⟹ open(?x)` from two examples, and already knows `{+sealed(?x)} ⟹ -open(?x)`. A sealed
hinged vault is a conflict; an unsealed hinged gate is not. **What should the corpus do about it?**

Measured four ways, and the answer is *nothing*:

| the learned rule concludes | precedence | vault | gate | ends |
|---|---|---|---|---|
| bare | `overrides` | `-open` | **never applies** | quiescent |
| bare | `supersedes` | `-open` | `open` | **runaway, 300 ticks** |
| **wrapped** | **none** | `-open` | `likely(open)` | **quiescent, 7 ticks** |

**`overrides` is too broad.** It is per TICK and per RULE, so one sealed object suppresses the
learned rule about *every* object — the gate is hinged and not sealed, and the agent still will not
conclude it is open. That is `rules.py`'s own warning about the two relations, arriving from the
acquisition side.

**`supersedes` is too narrow.** It defeats applications sharing a consumed **entry**, and two rules
reaching one conclusion from different premises share none: `<secret>` consumes `sealed(vault)`, the
learned rule consumes `hinged(vault)`. Nothing is defeated, and the two oscillate forever.

**So the third precedence relation this looked like it needed does not exist and should not.** A
learned rule concluding `likely(open(?x))` never contradicts `-open(?x)`, because they are different
propositions — the agent holds a generalisation *and* a specific fact at once, which is what it should
do. The conflict arises only if a corpus **crosses**, and then the corpus is the one asserting it and
can decline.

>**A learned rule that concludes wrapped cannot fight what the agent was told.**

**This is the grade deletion paying off somewhere nobody designed for.** *How strongly a rule may
speak* had to be **in the conclusion** for any of this to be sayable: with `@likely` it was a field
nothing could read, so a learned rule and an authored one wrote the same proposition and had to be
arbitrated. Two commits later the arbitration is unnecessary.

**And retiring on defeat is the blunt instrument.** `{+defeated(?l, ?w)} ⟹ {+dormant(?l)}` works and
throws away every case the rule was **right** about — measured: the learned rule was retired before it
ever applied. `defeated` is deduped per pair, so *how often* a rule loses is not askable, and the
corpus can only say *once is enough* — which this shows is wrong. **That** is where the credit walk
(`harmed`, which carries a count) belongs, and it is the next thing to try rather than a new relation.

## Latest: **precedence is READ, not kept** — the Python it took, deleted. Commit `authored`.

The user's question after `precede`: *why are we touching Python files, and not writing rules?* The
honest audit put the day's Python in three piles, and only one of them was debt.

| what | why it is Python | verdict |
|---|---|---|
| `Situation.add`/`drop`, the argument index, `walk_order`, `_kept` | optimisations of a semantics | §20's floor gate licenses them, and `ugm.state`/`ugm.arbitration` hold them to the slow definition every tick |
| `_adopt` | a **door, not a question**, beside `_dispatch` and `_enter` | argued |
| `generalise` | a function, so §17 says it **is** a tool | right by the design's own rule |
| **`_precede` + the precedence table** | **a cache of `overrides` facts** | **debt** |

**So the table went.** `RuleSet.precedence(relation)` reads what the graph claims, at the
position the agent is standing — exactly as `_recall` already reads `dormant`/`due`, with the same
argument: *cheap now; the moment it is not, this is an index, not a redesign.*

**Measured before deleting**, because the table had been kept for speed: the whole suite runs in
**6.42s against 6.38s**. It was buying nothing but the two ways it could be wrong.

What that deleted: `Machine._precede` (a write hook), `Machine._precedence_for` (a re-scan on
adoption), `RuleSet.overrides_rule`, `RuleSet.supersedes_rule`, both lists, and — one commit after it
was written — the whole *maintenance* problem those two hooks existed to solve. Precedence is now
dated and deniable because it is a claim, not because anything keeps a mirror of one.

**And the only thing in the suite that broke was a fixture calling Python.** Three checks, all from
`m2.rules.overrides_rule(a2, a1)` — a test reaching into a table instead of depositing a fact. That is
the whole answer to the question: the table was the anomaly, and the check that touched it was the
only thing that noticed.

`RuleSet.compose` inherits a constituent's defeats, and that is now a **claim the caller deposits**
rather than an append to a list — a `RuleSet` with no world to write in gets a composition with no
inherited precedence, which is the honest answer rather than a silent one.

Kill-probes: precedence read but never checked for being **claimed** (2 — a denial stops working);
`precedence` returning nothing (20).

**What is still Python and argued, for the record:** `_dispatch` and `_enter` are doors; `_forbid`,
`_widen` and `_notice_open` are §19's three guards; answerer bodies are what a tool *is*; and
`_in_play` is the one judgement `named` audited and left half-open — the goal half could be facts, the
delta half cannot on an append-only chain.

## Latest: **the agent harmonizes itself** — and the composition test earned its keep. Commit `precede`.

`defeated`, `adopt`, `generalise` and the wrapper story all landed the same day and had never met. §2
makes composition the criterion, so the fixture was built to make them meet: **learn a rule, adopt it,
find it fights a rule the agent already had, and settle the fight from inside.**

**It did not compose, and it broke in two places — both invisible until something tried to refer
to a rule.**

### 1. A rule could conclude a precedence and the arbitrator never read it

    rule <referee> = implies( { +p(?x) }, { +overrides(<cold>, <hot>) } )

The fact **held in the graph** and `rules.overrides` stayed **empty**: §14's precedence table was
Python state seeded by the **loader**, once, from the surface. §21's defect from the far side — not
*the machinery knows something no rule can ask about*, but **a rule says something the machinery does
not listen to**, which is worse, because the corpus is not even wrong.

It blocked both arcs exactly at their join: an agent reading `defeated(?l, ?w)` could not fix it by
raising a precedence, and a rule adopted at runtime could never be ordered against anything, because
the loader's table is keyed on names a corpus declared and an adopted rule has none.

So the table is maintained from the **write** (`Machine._precede`), and `Loader._maybe_precedence` is
deleted — *the fix is a deletion*, and doing both was the bug that found it: the pair went in twice and
one denial removed one copy. Precedence is now **dated and deniable** like every other claim, which is
what §14 says it is everywhere else.

**And the agent settles its own conflict**: it decides the precedence, the loser is defeated, and
the run reaches quiescence in **2 applications** where the unsettled pair oscillates for 60 ticks.

**A conflict starves the rule that would settle it.** `hot`, `cold`, `hot`, `cold` — and `<referee>`
never gets a turn. It needs `standing`, which is §19's carve-out for the fifth time. That is also the
loop-detection case, still unbuilt, now with a fixture that produces it on demand.

### 2. The adopted rule was a TWIN of the rule the graph described

`_adopt` called `RuleSet.rule`, which **mints** a node. So the tool described rule `942` and the live
rule was `979`: everything a corpus had said about the described rule went to a node that was not a
rule, and everything the machinery said about the live one named a node no corpus could reach. **The
twin trap, eighth time**, in code I wrote two commits ago — and nothing could see it until a standing
policy tried to order a learned rule and quietly did nothing.

    rule <trust-what-i-was-told> = implies( { +rule(?r), +adopt(?r) },
                                            { +overrides(<secret>, ?r) } )

That line is what the arc was for: **a precedence about a rule that did not exist when it was
written**, applying to whatever the agent learns. Two examples become a live rule, a standing policy
orders it under what the agent was told, the learned rule loses about the sealed vault, and the defeat
is on the record. Four commits, one run.

**And the author may say it in either order.** Written in the same consequent *before* the adoption,
the precedence lands while `?r` is not yet a rule and the write hook drops it — so `_adopt` re-reads
what the graph already says about the rule it is making live. §16's ordering trap, and here the author
has no way to see it: both orders read the same.

Kill-probes: no `_precede` (16), denial ignored (1), a fresh node for the adopted rule (4), no re-scan
on adopt (1 — and it was **0** until the either-order check existed).

**Two mistakes of my own in the fixture, both the same trap one layer out.** The learner closed
over the *first* machine's loader, so the second machine got node ids from the first — ints that mean
something else. And the check named an adopted rule with `kb.term`, which cannot parse a runtime rule's
printed form; it reaches one by **binding**, which is `artefact`'s finding from the other side.

## Latest: **there are no grades**. Commit `ungraded`.

The user's question — *do we really need `@likely`; can't a rule manage `likely(something)`?* —
measured rather than argued, and the measurement said yes three ways:

* **`ugm.modality` had already ranked the grade last of its three treatments.** Not a term, so **no
  rule can ask** *is this merely likely*; **no guard to cross**, because a grade annotates a
  conclusion the actor still sees and can ignore; **does not nest**. Lifting can be asked about and
  dies on generic rules (use/mention). Supposing wins outright.
* **Almost nothing used it**: **4 of 3,740 rules** authored a non-certain grade, **6 of 32,289
  entries** carried one.
* **Nothing ever decided on it.** `weaker` was called from exactly one place. The grade was
  **carried, composed, printed — and never obeyed**, which is this repo's own *read and not obeyed*
  defect arriving at the floor. It could not be obeyed, precisely because it is not a term.

So: `@` is refused by the parser (with a message saying what to write instead), `GRADES`, `weaker`,
`effective_grade`, `Member.grade` and `Entry.grade` are all gone, and `Entry` is back to **three
members and never a fourth**.

**The closed set went with it.** Five names Python knew became whatever modalities a corpus
cares to write, with whatever ordering it authors — §10's *closed is a rate, not a kind*, one place
further down.

**What replaces weakest link, and it was already built.** Cross `likely(p)` into a supposition, reason
bare inside with the ordinary rules — supposing *unwraps*, so nothing needs a lifted twin — and the
conclusion comes back out wrapped. Two uncertain premises give `likely(possible(c(t)))`: **the weakest
link as structure**, where `min` gave a number and forgot which premise was weak.

**What is lost, and it is a check rather than a caveat.** Weakest link was automatic and total.
Now nothing is concluded from an uncertain premise unless a corpus **crossed**, and collapsing the
nest is a corpus's table whose ordering is a corpus's claim: `{+likely(possible(?x))} ⟹ {+possible(?x)}`.
The ordinal stops being free and starts being arguable, which is the trade this design makes
everywhere else.

**And one thing the deletion bought.** Rule **composition** refused anything but `certain`, because
composing a grade is a minimum computed once from defeasible constituents — §16's objection one level
up. With grades gone the objection goes too, and the restriction was **deleted rather than solved**.

**It cost the two instruments that were built on it, and both got better.** `ugm.tools`'s *the
corpus's grade governs, not the tool's confidence* is now the corpus's **wrapper**, and the bare claim
is never asserted. `ugm.forest`'s credit walk needed two corpus lines saying **what this corpus is
willing to act on** — and that corpus turns out to be *reckless*, acting on a merely-possible
classification, which is what costs it the goal. Under grades that recklessness was **invisible**:
`<treat>` matched `is_gothic(?c)` whatever grade the entry carried, because nothing could read a
grade. Now it is one line, and deleting the line is how you get a careful agent.

`ugm.modality`'s grade column is now a **record rather than a measurement** — it cannot be run,
because there is nothing left to run it against. The probe that decided a deletion keeps its verdict
in prose, the way the deleted engine keeps its in git.

Kill-probes: conclusions leaving a frame **bare** (the replacement mechanism) — **61 failing**; `@`
accepted and silently ignored — 2. The design doc's own conditional is discharged in place: *if §9's
open question resolves toward wrapping, this argument needs re-running* — it resolved, and §12's
"where the grade lives" section now carries the re-run and the measurement.

## Latest: **an example becomes a rule**. Commit `generalise`.

Acquisition slice 2, in the seam `adopt` said it would be in. `rules.generalise` is Plotkin
anti-unification — **the dual of `unify`**, and the thing *learn from examples* is made of: matching
asks what two structures must agree about, this asks what they already do. `unify_patterns` was the
two-sided version of the first; nothing was the second, so the agent could recognise an instance of a
rule it had and never propose the rule from the instances.

Two examples in, one rule out, and it fires on a third case:

    fact +example(seen(door), known(door))
    fact +example(seen(window), known(window))
    fact +seen(gate)                      ⟹   known(gate) = + @likely

**One mapping across the premise and the conclusion, and that is the whole of it.** Generalised
separately they share no variable, so the rule concludes about something nothing binds. Generalised
together, `door`/`window` becomes one `?g0` on both sides and the result is exactly the rule a person
would have written. **One dictionary is the difference between learning and noise** — the kill-probe
that gives each half its own map costs 3 checks.

**What agrees is KEPT**, which is what makes it the *least* general generalisation: `f(a, b)` and
`f(a, c)` give `f(a, ?g0)`, never `f(?g0, ?g1)`. And one disagreement is one variable however often it
appears — `f(a,a)` with `f(b,b)` is `f(?g0, ?g0)`, not `f(?g0, ?g1)`, or the rule fires on pairs that
never matched. Both are kill-probed and both cost checks.

**The tool declines rather than generalising anything.** Two examples about different relations have
a *bare variable* as their least general generalisation — `{+?g0} ⟹ {+?g1}`, a rule that fires on
everything. Returning `None` is a real answer (§17), and the check is that nothing is adopted.

The learned rule concludes `@likely`, and that is §12 rather than modesty: a rule nobody authored is
exactly the kind whose conclusions must stay weaker than what it was told. It composes with the grade
work in `adopt` — the tool writes the grade, the door obeys it, and the derived entry carries it.

**A kill-probe crashed my own check instead of failing it.** A lazy generalisation returns a bare
variable, which has no member 0, and the check indexed one — *a runner has to be able to say False
about an absence*, fourth time in this file. Guarded, and `flat` now costs 5 checks.

**What is NOT closed, and it is the next slice.** The examples are corpus facts. The agent's own trail
is the richer source — every derived entry records what it consumed, and `rests_on` has been on the
graph since `support` — but `rests_on` is part of §12's **skeleton**, a plain relation instance that
nobody asserted, so ordinary rules do not match it and only stratum 0 can read it. Whether an ordinary
rule should see the skeleton is a real design question and not a small one.

## Latest: **a rule can author a rule** — the reverse-reify door. Commit `adopt`.

The acquisition arc's first slice, and the thing every item in the harmonization family was blocked on.
A rule has been data since §14's worked example — `rule(<R>)`, `conn`, `ant`, `con`, deposited at
authoring — and it went **one way**: `RuleSet.rule` was called by the parser, by tests, and by nothing
else. So the agent could answer *which rules do I have* and never *and now I have this one*, which is
why every amendment was a file edit.

    adopt(<R>)

**A door, not a question.** It belongs with `_dispatch` and `_enter` rather than with the six
answerers: `_dispatch` is where an intent leaves the agent, and this is where a rule enters it. What
decides that a rule is worth having is a corpus concluding `adopt(?r)`; what happens then is not a
judgement.

### The composer HAS to be a tool, and three walls say so

Hit in order, each a clean refusal rather than a silence:

* a `fact` may not contain a variable at all, so a corpus cannot write a rule's patterns;
* §8 scopes a statement's variables to it, so parts written on separate lines could not share a `?x`
  even if it could — the `excluded` wall again;
* a rule's consequent may carry only variables its antecedent binds, or the variables of an existing
  `<...>`-named rule — and a rule being *built* is not one.

So the corpus never names the new rule's insides. It reaches them by **binding**, which `artefact`
already established: composing is a function, and §17 says a request answered by a function is a tool.
That means slice 1 and *learn from examples* share one seam — anti-unification goes in the same
place.

**And the tool must build in the CORPUS's name scope.** My first composer used `g.atom("seen")`,
which mints; the rule it built was about a twin of `seen`, was adopted, was live, and matched nothing.
That is `Loader.answerer`'s own argument one level up — it made sure a tool answered the request the
corpus could *write*, and this is the same requirement for what the tool *builds*. **Anything that
binds a name has to go through the table that resolves it**, seventh time, minutes after I wrote the
sixth down.

### Two silent losses in `reify`, closed because this needed them

`ant`/`con` recorded neither the member's **position** nor the consequent's **grade**, so a rule read
back out of the graph was a different rule. Both are now members: `ant(<R>, pattern, sign, i)` and
`con(<R>, pattern, sign, i, grade)`.

Position matters because an antecedent is a sequence — §18's tiebreak reads the consumed entries and
`consumed` is filled by member position — and because `g.rel` interns, so a rule with two identical
members would have lost one. Reading them back in minting order would have reproduced authored order
by accident for anything `reify` wrote, so a check over it **could never have failed**; the fixture
deposits out of order on purpose. The antecedent carries no grade, and that is `Member`'s own argument
rather than an omission.

**Recording a grade and obeying it are two properties and needed two checks.** Adopting every
consequent at `certain` regardless of the graph broke **nothing** until the second one existed — *a
knob that is read and not obeyed is the same defect wearing the fix's clothes*, arriving where the
knob is a rule's own strength.

### Refused inside a supposition, and that is containment

§4 makes a frame's conclusions unreadable from outside by construction — the seat is a successor —
but `RuleSet.rules` is **one list shared by every frame**. A rule adopted while supposing would apply
after the frame is discharged, and to everything: supposing would change what the agent believes, which
is the one thing supposing must not do. `_dispatch`'s argument exactly. Refused on the record, naming
the supposition.

And the refusal is written **inside the frame**, so asking the root whether it holds answers `None`
however well it worked — containment caught my check before the check caught anything. It reads the
chain instead.

Four kill-probes, each in its own place: no door (3), no hypothesis guard (4), no position or grade
recorded (2), grade read but not obeyed (1).

**Next:** anti-unification in the same tool seam — two examples, one rule — and then the use/mention
question `defeated` surfaced (an intent naming a rule cannot leave the agent, because a rule node is
generic).

## Latest: **a defeat is on the record** — and the census that says what to build next. Commit `defeated`.

The user's decision to start on **knowledge acquisition and rule harmonization**, *because Cyc teaches
that is where the pain is*. Measured before choosing anything, and the measurement redirected the work.

### The census: `ugm.harmony`

Two questions — what *could* conflict (two rules whose consequents unify under opposite signs,
standardised apart) and what *did* (`_defeated` returning True on a real run):

| | |
|---|---|
| machines / rules / rule pairs | 187 / 3,645 / 33,989 |
| latent | 3,551 |
| ...where the unifier is a **bare variable** | **3,545** |
| ...genuinely specific | **6** |
| ...ungoverned by an authored precedence | **1**, and it is a fixture written the same day |
| `_defeated` asked / True | 19,341 / **22** |
| distinct pairs that ever fought | **4**, every one authored on purpose |

**There is not one unplanned conflict in this repository.** A static conflict detector shipped
today would report 3,545 false positives, one true positive already harmonized, and one that is a test
rule. It could not be gated by anything.

>**A corpus with no pathology cannot measure a detector for it.**

**The 3,545 are a fact about the bundle, not noise.** `<denial>` concludes `-?p` — a bare variable —
so it is in latent conflict with every positive rule in every corpus. No filter on the consequent
removes that; the real discriminator is whether two antecedents can hold at once, which is a join and
still only says *potential*. Static pair analysis is the wrong shape to start from.

So this is **not** evidence that harmonization does not matter — it is evidence that these corpora
cannot measure it. One author, days, dozens of rules; Cyc's pain is volume and many hands. The census
ships so the deferral stays revisitable: the day the last column is not zero is the day a detector can
be gated.

### What the census DID find: `defeated(<loser>, <winner>)`

Twenty-two defeats happened across the suite and **no rule could ask about one of them.** §21's defect
for the **tenth** time, and the purest case yet: `defeat` computes exactly this on every tick, uses it,
and throws it away — so *which of my rules actually fight* was a question about a run that no run
recorded.

**What ships is the occasion** (§19). What to do about a rule that keeps losing — ask its author,
raise a precedence, mark it dormant — is a corpus's, and the fixture shows one doing it.

**Written OUTSIDE `_choose`**, because `ugm.arbitration` re-runs that path against the same state and
its whole legitimacy is that neither side writes. An instrument that deposits has stopped observing.

**A defeat is not recorded when arbitration ignored it**: an `overrides` cycle defeats everybody, so
§14's fallback lets everybody through to keep arbitration total — and then nobody was defeated. And a
rule that merely **lost** the tick is not defeated either; losing is being deferred, not rejected, and
recording it would report an ordered rule base as a fighting one. Both are checks, and four kill-probes
each land on their own: no record (3), reversed pair (4), no cycle guard (1), no dedup (2).

**And the wall this fixture found, one line from where acquisition starts.** A corpus can conclude
`doing(ask(<hot>))` — *ask the author about the rule that lost* — and it **never leaves the agent**.
`_dispatch` refuses a generic intent (*a description cannot be acted on*), and a rule node is generic
by construction, since it holds the variables of its own patterns. So **every clarification request
about a rule is decided on and never emitted.** Recorded as a check rather than fixed: the fix is
§14's use/mention — the entry already carries `mention` — and that is a representation decision to be
scored, not slipped in. It is the first thing the acquisition arc has to settle.

**My census under-counted by 3.5× at first** — 53 machines where there are 187 — because it
remembered which machines it had seen as a set of `id()`, and CPython reuses an address the moment a
machine is collected. It reported **0 ungoverned** where the answer is 1. The conclusion survived; the
numbers it was argued from did not. And the suite now *contains* deliberate conflicts (an `overrides`
cycle, 120 defeats), so the actual-conflict rate can no longer be read off it — loop detection's
recorded trap, caused by the checks written for this very census.

**Next, decided:** acquisition first, Cyc's own order — the reverse-reify door (rules are readable from
the graph and not writable in it, so a rule cannot author a rule), then anti-unification as a tool so
examples become rules. Harmonization's detector comes after a workload that can falsify it.

## Latest: **a join is not a scan — the SECOND quadratic**. Commit `join`.

`pystrider` sent feedback (`../pystrider/docs/feedback_restart.md`) and its §1 is a finding this repo
had no way to reach: **there are two quadratics, and `quiet`, `weigh`, `heap` and `kept` all fix the
other one.** Everything measured here so far has been the *option set* — n ticks, each weighing what
could apply. Theirs has a **constant option set** and does its damage inside a single tick:

    rule <s1> = implies( { +child(?p, ?x), +child(?x, ?y) }, { +grand(?p, ?y) } )

**One tick cost 2,006,004 unifications over 1,000 facts**, with `proposed` at 18 and `applied` at
1. Reproduced here before anything was changed, and their diagnosis was exactly right: `candidates`
keyed on `(sign, relation)` and nothing else, so member 1 drew **every** instance of `child` for each
of member 0's N bindings.

| over 1,000 facts | `unify` calls | |
|---|---|---|
| as reported | 2,006,004 | |
| filed by argument too | 6,004 | |
| ...and the delta's pivot walked first | **3,003** | **668×** |
| the same, over a 1,000-node tree that actually matches | 4,994,004 → **6,993** | **714×**, 6.60s → 0.40s |

**Two changes, and the second matters as much as the first.** An entry is now also filed under each of
its arguments — `(sign, relation, position, node)` — and a member whose argument is bound looks there.
But an argument index is no use to the member that has bound *nothing* yet, so a pass pivoting on
member 1 still scanned the whole state for member 0, and a corpus deriving one fact per tick stayed
quadratic. **So the pivot is walked first**, and every other member is narrowed by what it bound.

**`pystrider` flagged the risky half correctly and it turned out not to be needed.** They asked
whether member order is free to be chosen, since §18's tiebreaks read the consumed entries. The
answer is that **the walk may be reordered and the antecedent may not**: `consumed` is filled by
member *position*, so §12's trail and `heap`'s stamp see exactly what authored order gives them. And
the narrowing itself removes only candidates `unify` would have rejected, so the matching candidates
and their order are **identical** — which is why nothing downstream had to change.

**Atoms only, and that restriction is load-bearing rather than cautious.** `unify` compares a
ground *structure* member by member, so it accepts a structurally equal node that is not the same
node — the twin trap — and an identity-keyed bucket drops those. Kill-probed: narrow on structured
members too and **4 checks fail**, all of them supposition checks, where the members are frames and
propositions. Filing them is also 4% of the suite for a bucket nothing can ever read.

**And one invariant here can be broken with the whole suite still green.** Filling `consumed` in
*walk* order instead of member order: **0 failing**, and `ugm.arbitration` cannot see it either,
because it compares two paths that would permute alike. So that one is asserted **directly** — a
match whose delta holds member 1's entry only, so the pivot-first walk actually runs. My first
version of that check handed it the whole state, where pivot 0 finds the application and the dedup
drops pivot 1's — so the walk under test never ran and the check passed vacuously.

**What it costs, stated rather than buried:** the `edge` chain 0.50s → **0.58s** at 1,600 (+16%), the
suite 6.20s → 6.39s (+3%). That is the price of maintaining the argument buckets on every deposit, and
it buys 300–700× on the shape `pystrider` says their whole corpus has.

**Their §4, also closed:** an answerer registered with the wrong arity raised
`TypeError: takes 2 positional arguments but 3 were given` out of `gate.write`, at the first write,
naming neither the tool nor the registration. It is refused **at registration** now, naming itself —
one place, so both doors get it — and `Loader.answerer` documents the protocol, since it is the door
every note tells people to use.

**Their §2 and §3 need nothing.** §2 is `weigh`'s *the benchmark that defined the wall is the
unrepresentative case*, derived independently from the other side — and their §1 is offered as a third
shape rather than the true one, which is the right reading. §3 adopts `artefact`'s *composing the text
is a function, so rendering is a tool*; the difference they name — their tool renders an artefact it
did not compose, so it is closer to `_verdict` than to a corpus function — is a real one and does not
change anything here.

## Latest: **the loop stops looking at the whole state — and it is LINEAR**. Commit `kept`.

The item the last handoff named: `heap` made the candidate walk linear and the runtime stayed
quadratic, because `Situation.__init__` (3.37s / 2,403 calls) and `_in_play` (2.31s / 1,202) are both
**O(state) per tick**. Both are gone, and the shape of the fix is `state`'s own argument one layer up:

>**Keeping the state and then rebuilding everything read off it keeps the cost you were paying.**
>§4 says a state changes by one claim at a time, so the index over it changes by one claim at a
>time, and so does what is read off it.

| n | before today | **now** | ticks / writes / considered |
|---|---|---|---|
| 400 | 0.40s | **0.12s** | identical |
| 800 | 1.28s | **0.25s** | identical |
| 1,600 | 4.79s | **0.48s** | identical |
| 3,200 | — | 0.98s | |
| 6,400 | — | 2.07s | |
| 12,800 | — | **4.13s** | |

**Doubling now doubles.** Eight times the corpus costs less than 1,600 facts did this morning,
and the profile has no O(state) call left in it at all — `Situation.__init__` and `_in_play` are not
in the top eighteen. The suite is 1.15× too (6.78s → 5.89s), so this is not a big-corpus concern
either.

Three things are maintained where the state is, by the same one-claim-at-a-time walk `_kept` already
ran:

* **`Situation` gained `add`/`drop`** — the matcher's index, per sign and relation. The constructor
  stays for the callers that genuinely have a fresh list (the delta, the instrument).
* **`_state()` is a view**, materialised only when something asks for the list. The loop never wanted
  one: it wants the Situation, and building a list to build an index from was pure ceremony repeated
  once a tick.
* **`_in_play`'s two halves accumulate differently, and finding out why is the finding.** The delta
  half is a running union over a cursor — a moment's delta only grows. The goal half is a **count**.

**"A goal is never denied" was written in this repo as the reason the goal half is monotone, and
it is a claim about the fixtures rather than about the design.** `{+nearer(?x)} ⟹ {-goal(nearer(?x))}`
is an ordinary rule. So the keys are counted, not unioned: two goals can put one relation in play and
one of them going away must not take the other's key with it. That denial is now a check, and without
it nothing in the suite could tell a maintained key set from one that never forgets.

**`ugm.state` — §20's floor gate for the state**, beside `stratum0` for the read and
`ugm.arbitration` for the move. The walk stays as the slow definition and the kept state is held to
it on **every look, in every fixture: 7,288 looks, 0 disagreements** in three columns.

| break | the suite | state | index | keys |
|---|---|---|---|---|
| never drop a superseded entry | 2 | 806 | 806 | 0 |
| never decrement a goal's key | 1 | 0 | 0 | 8 |
| never invalidate a bucket's read | 29 | 0 | 3,884 | 0 |
| rebuild the state newest-first | 6 | 6,456 | 6,456 | 0 |
| **one key cache for every seat** | **0** | 0 | 0 | **1,597** |

**The suite cannot see the last row, and that is not a gap in the fixtures.** Wrong keys make a
worse choice, never a wrong conclusion — and every fixture asserts an outcome the loop reaches
anyway. *Nothing that asserts what the agent concluded can see what it was thinking about while it
concluded it.* That is the whole argument for the third column existing.

**Three instrument bugs of my own, and all three are traps already written down here.**

* **The instrument read `self._in_play`** — so it compared each of the five deliberate mutants in
  `what_the_situation_is_about` against the definition and reported **90 disagreements**, every one a
  fixture doing its job. `ugm.bundle`'s trap from the other side: *a comparison instrument cannot
  read a mutation the fixture already talks about.* It captures the shipped method at install.
* **My new check could not fail: it asked machine 2's key set about machine 1's node.** A graph per
  machine means `nearer(a)` is a different node in each, so `wanted not in forgotten` was true
  whatever happened. The twin trap, arriving from the two-fixtures side — and it took a kill-probe
  that *failed to bite* to find it.
* **The index column compared `_by` rather than `candidates`**, so it could not see a bucket read
  back in the wrong order. Asked through the read path now, with a stand-in graph rather than a
  minted variable: an instrument that mints nodes is depositing in the graph it is measuring, and
  node identity is the arbitration stamp.

**And the honest limit, measured rather than assumed:** reversing the **state** breaks 6 checks;
reversing the **buckets** breaks none. Since `heap` the within-rule order is a stamp off the consumed
entries' nodes rather than the order they were discovered in, so nothing downstream reads a bucket's
order. The reversal is kept because it is what the walk says and this replaces the walk — not because
a check would notice. `ugm.state` is what notices.

**What is next, unchanged:** loop detection, designed and measured below and still not built.

## Before that: **the last two hats — support, and reconsidering a binding**. Commits `support`, `binding`.

Both of the arc's remaining open items, and both turned out to need less machinery than their
reputation. The user settled the two design questions: **the reaction to lost support belongs in a
corpus**, and **exclusion is its own relation rather than a re-read denial**.

### Support: the third negative existential, and it deliberately does nothing

    rests_on(<entry>, <entry>)     what an entry was derived from -- STRUCTURAL
    support(p)                     a request, asked by a corpus rule
    unsupported(p)                 the answer, deposited only when nothing does

**`rests_on` is skeleton, not entries.** It joins `pred`, `in_delta` and `delta_next`: nobody
asserted it, it cannot be denied, dated or attributed, because support is *how the entry was made* and
not a claim about the world. It was already recorded as `Entry.consumed` — a Python tuple, so no rule
could ask what anything rested on. **§21's defect for the ninth time**, closed the way the other eight
were. (It also made `entry_by_node` a dict lookup instead of a scan of every delta ever.)

**And the machinery does not retract, which is the decision rather than an omission.**

>**Losing your reason is not acquiring a counter-reason.** A discredited source does not make what it
>told you false; it leaves you without a reason, which is a different state and the one you can act
>on. An engine depositing `-p` here asserts something nothing justified, and §12's weakest link
>acquires a link with nothing behind it.

Grepped before proposing it, and it was **already true**: no write hook in `machine.py` or `gate.py`
deposits a `-`. Every denial in the graph comes from an authored rule or a corpus fact. So what ships
is the occasion; the reaction is one line and there are at least four sensible ones:

    {+unsupported(?p)} => {-?p}   /  {+goal(?p)}  /  {+doing(ask(?p))}  /  nothing

**Asked, never volunteered** — `blocked`'s reason exactly: a proposition may rest on several things,
so one withdrawal says nothing until the rest are looked at. Legitimate at `quiet`, a lie before it.

**Unsupported and false differ in BOTH directions**, and that is checked: a denied *fact* is not
unsupported, because it was asserted and so never had a reason to lose. Five kill-probes, each biting
its own checks — including one that makes the machinery retract, which breaks precisely the check
recording that it must not.

### Binding revision: the missing piece was *what has already been tried*

    excluded(<plan>, ?v, x)     not that one

A `binds` fact was always deniable; denying it achieved nothing, because `_settle` re-unifies and picks
the same first candidate. **The gap was never a way to withdraw a choice — it was a way to say what
had been tried.**

**And both halves are needed; either alone is worse than neither.** Measured three ways on two
viable taps:

| | `?t` | |
|---|---|---|
| nothing reconsidered | `butt` | quiescent |
| **exclude only** | `butt` | **inert** — the surviving binding pins the variable before the exclusion is consulted |
| **deny the binding only** | `butt` ×270 | **runaway** — the same candidate chosen and denied forever |
| **both** | `butt` → **`sink`** | quiescent, 29 ticks, goal reached |

The runaway is `reask`'s criterion in a **third** place — *an occasion warrants a re-ask only if
re-asking cannot produce one* — with the binding as the occasion the re-ask itself recreates.

**And the exclusion cannot be a corpus FACT.** §8 scopes a statement's variables to it, so the `?t`
in `fact +excluded(plan(<pour>, water(kettle)), ?t, butt)` is a different node from the `?t` inside
`<pour>`, and it excludes nothing. It has to be **concluded by a rule**, which binds the plan's own
variable through `binds`. Same wall as a norm not being revisable from the surface, reached from the
binding side; kept as a check.

**The recovery rule is keyed on `quiet`**, which is the user's framing and is the safer one: the loop
has finished, so reconsidering cannot starve anything still due to run — the same argument that makes
`blocked` legitimate there.

    rule <redo> = implies( { +quiet(?m), +binds(?p, ?v, butt), +subgoal(?p, ?s) },
                           { +excluded(?p, ?v, butt), -binds(?p, ?v, butt),
                             +again(check(?p, ?s), ?m) } )

### ...and the hole that stopped the two halves joining up. Commit `consumed`

**`_settle` built its env by READING the plan's bindings and never consumed them.** So a
conclusion that relied on *which tap* did not rest on the entry that said which tap. R5 says every
entry has a licence and a source; §12 says a conclusion is no stronger than what match consumed. Both
were true here and **both were vacuous**, at the one place a plan commits to something.

Three consequences, and only the third would ever have been noticed by reading output:

* `unsupported` could not see a withdrawn binding — so *reconsider a binding* and *notice what rested
  on it* did **not** compose, which is the entire reason for doing them in one arc;
* §12's weakest link could not weaken a conclusion by the grade of the binding it assumed — a
  `@possible` tap laundering into a `@certain` achievement, the exact failure `effective_grade` is for;
* `why()` never mentioned which tap it had assumed.

Fixed, and now they compose: withdraw the binding and the sibling's `achieved` is reported
`unsupported`; with it intact, nothing. Only the bindings the goal actually **uses** are consumed —
consuming the whole env would make every sibling's conclusion rest on every other sibling's choice,
which is the opposite of what plan bindings are for. Kill-probed: with bindings unconsumed, 2 checks
fail. And the fixture had to ask on the **denial** rather than at `quiet`, because two rules keyed on
the same occasion run in authored order and the question was being answered while the binding still
held — §16's ordering trap, in a fixture this time rather than in the engine.

## For the next session: **loop detection, designed and measured, not built**

The remaining gap, and the user's design for it. Every occasion this agent has is a record of
**stopping** — `quiet`, `left`, `stopped`, `widened`, `reached`, `bounded` — and **a loop is the
failure to stop**, so none of them ever fires. Measured on the deny-only runaway: 800 ticks, final
state `applied`, never once `quiet`.

**The user's proposal: rhythm detection.** Check whether the recent sequence of applications repeats
at period 1, 2, 3…, with the maximum period rising as a subgoal drags; and gate an expensive
state-comparison behind a cheap rhythm hit. That escalation is the shape `_widen` and `_recover`
already have — *escalate before believing the cheap answer* — here mirrored as **escalate before
believing you are making progress**.

**Measured before building, and the measurement changed the design.** Sequence of `(seat, rule,
bindings)` per applied tick, periods 1..8, over the whole suite:

| | period 1 | periods 2–8 |
|---|---|---|
| **62 healthy machines, 2,038 applications** | **0** | **0** |
| the deliberate deny-only runaway | 272 | 0 |

* **Phase 1 alone is a perfect discriminator here** — zero false positives. So the cheap filter is
  not a filter, it is the whole test.
* **Do not build phase 2.** Net-effect-nil was a fix for a false-positive problem that does not
  exist. The deletion arrived before the code did, for once.
* **The SEAT must be in the key.** Without it the same rule applying inside a hypothesis and outside
  it reads as a repetition — 4 false positives, in the `explains`, `suppose` and `doing` fixtures. An
  application repeated in a different frame is not a repetition.
* **My first measurement was contaminated twice** and read as a strong negative result (12% of
  applications flagged, phase 2 confirming 98%). Both were the instrument: no seat in the key, and the
  suite now *contains* deliberate runaways, so it cannot measure a runaway detector's false-positive
  rate without splitting them out. **A fixture that contains the pathology cannot measure the detector.**

**What to build:** rhythm per seat over periods 1..`period(n)`; `period(n)` a **knob-fact** with a
Python default, so *deepen the search when the subgoal drags* is a corpus rule
(`{+bounded(?w)} ⟹ {+period(8)}`) rather than a curve in the interpreter — the move `<care>` already
makes with `tolerance`. Deposit `circling(<seat>)`, deduped like `widened`; **do not stop the loop**,
for `_notice_open`'s reason. Read the sequence from the chain (licences are already on every entry) so
it does not become instance #10 of the hidden-state defect.

**And write a 2-cycle fixture FIRST.** The suite contains exactly one loop of one kind, so
"period 1 is enough" is a claim about a sample of one, and a longer-period detector shipped today
would be **unfalsifiable** — no check could tell whether it worked.

**Also still open:** whether the bundle should ship generic recovery rules of the `<redo>` shape at
all. The user's framing — recovery keyed on `quiet` — is right for every failure except this one.

## Before that: **build it, see which half is right, repair the other**. Commit `artefact`.

The user's case: *write an `ls` + `grep` that finds all Python files containing a class definition* —
can the agent make a first attempt, reread it, notice it satisfies **find the Python files** but not
**containing a class definition**, and fix that half? `python -m ugm.artefact`, 11 checks.

**Yes, and nothing had to be built.** The goal is a conjunction, so backward reading splits it and
`check` answers each half separately — *that per-conjunct answer is the whole of what a partial
result means here.* The repair is one rule keyed on `unmet`, and the control is the discriminator: it
fires on the `ls`-only attempt and **not** when the command already does both.

**The artefact is a node; what it DOES is claims about it.** The goal decomposes over
`finds(?c, py_files)`, never over shell syntax — which is what makes the repair a rule instead of a
string edit, and why rendering is a **tool**: composing text is a function, and §17 already says a
request answered by a function is exactly what a tool is. Measured at that boundary: the string lands
as `answered(<render>, spell(cmd), …)`, delete the trust rule and it is still on the record and
believed by nobody, and a corpus can retire the renderer.

**The finding, and it is a defect this file has now recorded in a third place: the
partial-satisfaction signal is STALE.** Out of the box **both** halves report `unmet` — including the
one satisfiable from the start — because `check` is asked the moment a subgoal appears, before
anything is derived, and nothing asks again. So the repair fired for the right half only because the
author happened to name it; a symmetric rule for the other half would have fired too, wrongly.

| | ticks | halves recorded as achieved |
|---|---|---|
| as shipped | 43 | **none** |
| plus one `<recheck>` line | 46 | both |

`{+unmet(?p, ?sub), +?sub} ⟹ {+again(check(?p, ?sub), ?sub)}` — the `again` machinery from `reask`,
no new anything. Nothing ships concluding it (§19: what ships is the occasion, not the reaction), but
this is now the **third** place the same gap appears — `achieved` going stale mid-plan, escalation not
re-asking a dormant-period `blocked`, and this. Worth reconsidering whether the bundle should carry it.

**And a limit found by writing a check: a tool may return something no corpus can name.**
`kb.term("answered(<render>, spell(cmd), ls *.py | xargs grep -l '^class ')")` is a **ParseError** —
stars, spaces and quotes are not term syntax. A rule reaches the rendered artefact by **binding**
(`?s`), which is all any rule needs; what is impossible is a rule mentioning one particular rendered
string literally. Same wall as a norm not being revisable from the surface, and it lands exactly where
the values stop being the corpus's vocabulary and become someone else's.

**Scope decision, recorded: bidirectional surface is NOT next.** Generation is a tool and is now
demonstrated; the engine's own language already round-trips (`rendered`, byte-identical across four
hash seeds). Parsing domain text is the intake seam — **0/50 on raw prose, 26% on a book corpus** in
the previous arc, and `ugm.workload` calls it a seam with no algorithm at all. That is where a model
belongs and it is a different project. Next is `_in_play`/`Situation`, then binding revision.

## Before that: **the agent stops looking at its whole option set**. Commit `heap`.

`weigh` measured that there was nothing left to *withhold* — 99.6% of candidates genuinely apply. So
the move was to stop **looking**, and three measurements made it possible, each taken before it was
used:

* **The arbitration key is per RULE.** `rules.arbitrate`'s key is `(score(rule), rules.index(rule))`
  and holds nothing about the application — so there are |rules| priorities, not n. My earlier worry
  that a heap would re-key n candidates every tick was simply wrong about where the key lives.
* **The within-rule order is a stable stamp.** An entry's node is minted from a monotonic counter, so
  descending node order reproduces most-recently-claimed-first exactly: **0 disagreements over 2,452
  ticks**, against an inverted control that disagreed about **686 moves**. And the one structurally
  different case — a consumed entry not in the current state — occurred **0 times in 51,199
  candidates**, because invalidation retires those applications first. Reachable only through
  dormancy; no fixture produces it, and that is the fixture to write if this is pushed further.
* **Nothing needs the whole list.** `_note_doubt` reads the rivals' *rules*, which rule order gives
  in rank order; `_forgo` reads candidates sharing a want, which is an index (`by_want`).

**So: rules in rank order, each rule's candidates in stamp order on a heap, validate at the top, step
to the next on rejection.**

| n | before today | after `quiet` | after `weigh` | **now** | candidates weighed |
|---|---|---|---|---|---|
| 800 | — | — | — | **1.35s** | 1,600 |
| 1,600 | — | — | ~16s | **4.70s** | 3,200 |
| 3,200 | — | — | — | **18.88s** | 6,400 |

**The candidate walk is now LINEAR: `considered` went from n²/2 to exactly 2n** (500,000 → 2,000
at n=1,000), with ticks and writes identical throughout.

**And the runtime is still quadratic — ~4× per doubling.** The candidate walk is no longer the
cost. Profiled: `Situation.__init__` (3.37s / 2,403 calls) and `_in_play` (2.31s / 1,202 calls), both
**O(state) per tick**. `_state()` is built incrementally since `state` but still *materialises a list
of the whole state every tick*, and `_in_play` scans it again for live goals. That is the next layer,
and `_in_play`'s half is already known to be easy — goals are never denied, so the live-goal set is
monotone and needs no invalidation at all.

**Two bugs of my own, both in the lazy machinery, and neither about heaps.**

* **A heap that keeps its dead is walked past them every tick.** The first version re-pushed withheld
  candidates so they would keep their place, and measured **721,800 heappops over 1,202 ticks** —
  the quadratic wearing a heap's clothes. The heap now holds only what is live, and `_revive` pushes
  back.
* **`GeneratorExit` runs at the `yield`, not after it.** The consumer `break`s the moment it has
  its move, which closes the generator — so the line after `yield` that returned the chosen candidate
  to its heap never ran, and the winner was silently dropped from the heap for every later tick.
  **29 checks failed, not one of them about heaps.**

**`ugm.arbitration`, and it is the point of the commit as much as the speed is.** `_choose` is an
optimisation of a semantics, so §20's floor gate applies: `_materialise` keeps the slow definition —
every live application, defeated, filtered, in arbitration's order — and the instrument compares
**move, doubt and forgone** on every tick of every fixture. **2,636 ticks, 1,934 with a move, 78 with
a rival, 0 disagreements.** Kill-probed three ways, each landing in its own column: take the second
survivor (423 move + 423 doubt), drop `_sharing` (6 forgone), drop the rivals (76 doubt).

**A check of the suite's own was measuring the implementation, not the property.** *The apparatus
wins most of the agent's choices* spied on `arbitrate`, which the chooser stopped calling — so its
tally went to zero and it passed **vacuously**. Re-pointed at the move that was made. An instrument
keyed on which function the loop happens to call is keyed on the implementation.

## Before that: **the quadratic is ARBITRATION, not bookkeeping**. Commit `weigh`.

Went after the exponent by withholding the no-op applications from the candidate list — the move
`quiet` named, whose blocker was that `defeat` must keep seeing them. Built it, and **the measurement
refuted the premise it was built on.** On the scaling fixture there is almost nothing to withhold:

| n | candidates considered | `_would_change` **True** | False |
|---|---|---|---|
| 200 | 20,300 | **20,100** | 200 |
| 500 | 125,750 | **125,250** | 500 |

**99.6% of candidates genuinely have work to do.** With 1,000 independent `edge` facts the agent
really does have 1,000 applicable rules on tick 1, 999 on tick 2, and §18 lets it make one move at a
time — so it weighs n, then n−1, then n−2. **The n²/2 is the option set, not waste.**

>**The agent recomputes its option set on every move because the option set IS different on every
>move.** Nothing that makes each candidate cheaper — an index, a verdict cache, withholding — can
>change that. The only levers are a ranking maintained incrementally across ticks, or applying more
>than one rule per tick, and the second is §18's *nothing owns the loop* being sold.

**And the benchmark that defined the wall is the unrepresentative case.** The same count over the
whole selftest suite — 56 fixtures of the kind anyone actually writes:

| | True (has work) | False (no-op) |
|---|---|---|
| the `edge` chain | **99.6%** | 0.4% |
| the whole suite | 10.6% | **89.4%** |

One rule with n independent instantiations is the *maximum* of independent applicability, which is
exactly what this loop is worst at. It is a fair worst case and it was read as a typical one.

**What shipped anyway, because it is right where corpora actually are:** applications withheld once
known to be no-ops, revived when something they read changes. **1.16× on the suite, 1.3× on the
scaling fixture**, 390 checks identical. The `defeat` split it required is the part worth keeping
regardless — `defeat` now takes the matched **rules** separately from the candidate **applications**,
so the two can come apart without §12's guarantee coming apart.

**Three kill-probes, all caught by checks that already existed** — no new ones were needed, which is
the sign the guarantee was already pinned. Give `defeat` only the live candidates: **3 failing**,
precisely the *boss's rule obeyed once, then undone by the vice's* case `rules.py:617` describes. Ask
the cycle fallback of the short list instead of the rule set: **1 failing**. Take the fast path when
`supersedes` is in use: **1 failing** — it compares consumed entries, so it cannot be answered from a
list something may be missing from, and that path keeps the old cost by design.

## Before that: **the option set is remembered — 2×, and the exponent is UNCHANGED**. Commit `quiet`.

**Read the second half of that headline first. I set out to buy the exponent and bought a
constant factor**, and the measurement says so plainly rather than being framed around what did work.

Measured **before** building, on a chain of `edge` facts:

| facts | ticks | `_would_change` calls | re-tests returning the **same** answer |
|---|---|---|---|
| 200 | 202 | 40,400 | 99.0% |
| 500 | 502 | 251,000 | 99.6% |
| 1,000 | 1,002 | 1,002,000 | **99.8%** |

Third instance of one observation — `delta` found 98.7% of matching was re-derivation, `state` found
the walk rebuilt what a delta could extend, and this is *nothing remembers that this question was
already answered*. So the verdict is kept beside the applications, in the same cache, retired by the
same discipline: a verdict reads only the propositions the application would write, so a fresh entry
about one retires it, a fresh `forbidden`/`refused` flushes the lot, and a fork misses.

| facts | before | after | | ticks / writes |
|---|---|---|---|---|
| 200 | 0.72s | **0.40s** | 1.8× | identical |
| 1,000 | 17.19s | **8.81s** | 2.0× | identical |
| 2,000 | 65.79s | **34.90s** | 1.9× | identical |

**And 10× the facts still costs ~87× the time (it was 91×).** The profile says why, and it is
structural rather than a missed optimisation: every top entry is called **1,002,000 times ≈ 1,000
applications × 1,002 ticks**. `_applications` returns the *entire accumulated set* every tick, and
`tick` then runs five O(candidates) passes over it — `defeat`, `_passed_up`, `_would_change`, the
sort, `_wants`.

>**Caching a verdict removes the cost per candidate. It does not remove the candidate.** The loop is
>quadratic because it re-examines every application it has ever found on every move, and no amount
>of making that examination cheap changes the shape.

**What the measurement corrected on the way.** I assumed the cost was the chain walk. At 1,000
facts: `_forbid` 5.31s, `substitute` 3.94s, `resolve` **1.10s** — the walk is the smallest of the
three. The cache was still right, because it skips all three; but *optimise the walk* would have
bought the least of them, and I would have measured the win and believed the theory.

**The next move is named, and so is its blocker.** Withhold the cached-`False` applications from the
list instead of re-filtering them, so a tick's candidate set is O(new + revived). The blocker is
already documented at `rules.py:617`: `defeat` runs **before** the quiescence filter on purpose,
because *defeat is about whose antecedent holds, not about who still has work to do* — filter first
and the winning rule vanishes once its conclusion is written, leaving the loser unopposed to
overwrite it. So `defeat` must keep seeing the whole set while the other four passes see the live
subset, and that is the next commit rather than this one.

**Kill-probed, three ways.** Bypassing the cache entirely: **390, 0 failing** — the control, and
what makes this an optimisation rather than a change. Never retiring a verdict: **103 failing**.
Not flushing on a fresh norm: 6 of the norm checks fail in isolation, and the full suite **livelocks**
— which is precisely what `_would_change`'s own comment says the refusal record exists to prevent.
No new check was needed; the invalidation was already gated by checks written for the norms.

## Before that: **the sanity check — would a Rust port have to reason?** Commit `named`.

The user's question, and answering it honestly meant auditing rather than asserting. **Mostly no.** A
port is `graph`/`chain`/`gate`/`rules`/`tick` — five primitives, nine write-hooks, three guards, a
parser — and every policy is `bundle.ugm` and the corpus. The three refusals and the six answerers
are each argued. Two things were **not**, and both are now closed.

**`_in_play` was the one judgement in the loop nobody had argued for.** §19 says a row is
*matched when that key is in play* and never said what **in play** means. Measured five ways, on the
smallest fixture that can tell a goal-serving rule from a useless one:

| `_in_play` returns | first move | whole suite |
|---|---|---|
| **as shipped** | `toward` | 0 failing |
| nothing | `wander` | 9 |
| the delta only | `wander` | 7 |
| goals only | `toward` | **2** |
| everything the state asserts | `wander` | 7 |

>**The key is not a subset of what is asserted.** Nothing ever claims `nearer(a)`; what is claimed
>is `goal(nearer(a))`. A pass over every proposition *and* every relation in the state — strictly
>more than the shipped key — still misses the node the preference is keyed on, because the key
>reaches **inside** a proposition for its argument. More is not nearer.

**And the two halves are not one idea.** The goal half carries seven of the nine checks; the delta
half carries two, both about the recall **budget** rather than arbitration. They differ in kind too:
a goal is never denied, so the goal half **already accumulates**, while the delta half is genuinely
per-moment. So *make the key facts* is **half available** — the delta half could not be, on an
append-only chain; the goal half already is in that condition, and whether it should move is now open
rather than closed. I first said the transience argument killed the whole idea; it kills one half.

**`concluded(<frame>, <what>)` — §21's defect for the EIGHTH time**, found by reading the
deleted `ugm/hypothesis.py`. Its `rivals(about)` made coexisting rivals the headline advantage over
one-at-a-time supposition; this floor kept the coexisting and lost the comparing. Every crossed
conclusion has carried the licence `concluded(<frame>)` since discharge was written — so `why()`
could always answer *which hypothesis produced this*, and **no rule could**, because a licence is a
field on the entry. Same fix as the seven before it: deposit the record.

    { +left(?f, ?a), +concluded(?f, likely(nopressure(tap))) } ⟹ { +explains(?a, nopressure(tap)) }

The fixture is two diagnoses that **agree** on a wet floor and differ on one prediction, because
rivals that disagree about everything need no comparing. Four kill-probes, each failing exactly its
own check: dropping the deposit (4), recording only `concluded(<frame>)` without the what (3), and
taking it out of `_bookkeeping` (4).

**Two instrument bugs, both this repo's own recorded traps, in checks written minutes after
discussing them.** Rival frames were compared by `g.show` — and every frame prints as
`frame(moment(), moment())`, so a set of names collapsed two rivals into one; **the twin trap, seventh
time.** And the arity-1 mutation **crashed** the runner instead of failing it, because the check
indexed member 1 unconditionally — *a runner has to be able to say False about an absence*, third time.

**And one check could not fail: the bookkeeping one.** Asked of the rivals it is vacuous — they
are **siblings**, so every `concluded` record is written at the root and no wrapper is ever in a
position to reach one. It needed its own nesting fixture. *A fixture can only see a filter that its
rules can reach*, recorded about a one-member antecedent, arriving again from the frame side.

**What the two deleted modules settle about the port.** `query.py`'s `is_pure` — 45 lines of
transitive static analysis proving a function never reaches the world — was **not ported, it was made
unnecessary**: there are no function bodies, and `_hypothetical` refuses to dispatch inside a
supposition. `hypothesis.py`'s `variant`/`backup`/`restore` went the same way: an append-only chain
has nothing to back up. One thing did **not** survive and is now named: `refutes` handled
*incompatibility*, and this floor has no vocabulary for it — you can deny a proposition, you cannot
say two propositions are incompatible.

## The day in one page

Eleven commits, and the shape of them is worth more than the list. **Two of the three things that
looked like features turned out to be Python being deleted**, and the two biggest wins came from the
user's proposals rather than from the plan.

| commit | what it settled |
|---|---|
| `reask` | `again(<req>, <occasion>)` — the ENTRY needed to be fresh, not the request |
| `cooking` | all six apparatus answerers bound by `answers(<M>, ask)` facts; 4 are `standing` |
| `survey` | the two sibling consumers are dark, and the wall is scale — measured |
| `delta` | matching keyed on the delta — **98.7% of it was re-derivation**, and 92.9% at fixture scale |
| `scopes` | a scope can span documents; **bounded references make coreference ABSENT, not solved** |
| `state` | the resolved state kept, not rebuilt — 8.3x, and 3 of 4 mutations were invisible to 323 checks |
| `domains` | `dormant(billing)` — **14.5x from one corpus line**, the strongest lever measured |
| `escalate` | a dry search reaches for what is out of mind, but only with a goal outstanding |
| `report` / `persist` / `rendered` | a door (`python -m ugm`), and a session saved as **what it was told**, rendered from the graph |
| `knobs` / `effort` | the last hidden state: bounds are claims, and the agent's own effort is **reasonable over** |
| `reenter` | a hypothesis can be thought about again — by **removing** the Python that stopped it |

**Three recurring shapes, each of which paid more than once today.**

1. **The fix is usually a deletion.** `reenter`'s dedup was redundant with quiescence; my first
   repair added a Python test and was worse. `rendered` deleted a journal that duplicated the chain.
2. **A check that cannot fail is the default, not the exception.** Kill-probing found ungated
   lines in *every* commit: 3 of 4 in `state`, 3 of 4 in `domains`, 3 of 5 in `effort`. Twice the
   suite could not see a genuine soundness hole (concluding from a denied premise; a knob read and
   not obeyed).
3. **My instruments lied twice, both by reading silence as a result.** A buffered stdout made a
   12.7s run look like a timeout and produced a headline 20x too flattering; a probe counted `FAIL`
   lines and read a crash as clean.

Branch `restart`, pushed. `main` still holds the old 46-module engine on purpose.

## Latest: **a request can be re-asked**. Commit `reask`.

The item the last handoff ended on — *the single thing standing between the agent and noticing both
its own satisfied goals and its own dead rules*. It cost a wrapper and one write, and **the diagnosis
everyone had been carrying, including mine, was half wrong.**

**The request never needed to be fresh. The ENTRY did.** §6 said *an entry once written is
permanent, so restating it changes nothing* — true, and irrelevant: `Chain.deposit` has always taken a
second entry about a proposition it has seen, because that is what §10's two indices are *for*. What
forbids the re-ask is `_would_change`, and it forbids it **of a rule**. The machinery re-delivering a
request is not a rule restating one, so the prohibition never covered the act at all.

    again(<request>, <occasion>)     ask this again, because of this

An ordinary node, different per occasion, so concluding it **is** a step. What the machinery does with
it is write the wrapped request **through the gate** — and `_settle`, `_fit`, `_verdict`, `_root` and
`_answer` are all `on_write` hooks, so a re-asked request reaches all five and **not one of them knows
re-asking exists**. The contrast pair the `rooted` section below ends on, closed:

| | goal holds | `achieved`, no re-ask | `achieved`, re-asked |
|---|---|---|---|
| holds from the start | `+` | `+` | `+` |
| derived a few ticks later | `+` | **None** | **`+`** |

One tick dearer (15 → 16). The no-re-ask row is kept as its **control**; the two runs differ by two
corpus lines and nothing else.

**Two things fell out that were not designed for.**

* **Retry is a corpus rule**, which §21 wanted and had nothing to retry with. `again(doing(a), occ)`
  re-delivers an intent, and `_dispatch` dedups on the **entry** rather than on the proposition — so
  the act leaves the agent a second time. Measured: `['open(door)', 'open(door)']`, with the un-stuck
  door as the control that opens once.
* **A tool is re-askable by the same line.** A stub that declines the first asking answers the second.
  That is §2's composability criterion rather than a convenience: re-asking and answering were designed
  against each other by nobody.

**And *when* is not free choice — this is the finding to carry.** An occasion the re-asking can
itself produce warrants the next re-ask, which produces the occasion after that:

>**An occasion warrants a re-ask only if re-asking cannot produce one.**

The author picks the trap or avoids it with **one word**, and neither reading of the word is about
re-asking. `quiet` is deposited once per seat, and an `implies` rule does not move the seat:

| `<recheck>` written | ticks | askings | ends |
|---|---|---|---|
| `implies` | 16 | **1** | quiescent |
| `causes` | 300 (the limit) | **143** | still going |

`causes` moves the seat, which mints a fresh `quiet`, which warrants the next re-ask. I expected the
`implies` version to run away too and it does not — measured rather than reasoned about, and the
criterion is **stated and not enforced**: nothing stops an author writing the second one.

## ...and the same commit: **the apparatus eats its own cooking**. Commit `cooking`.

The user's *shall we complete the de-pythonization?* — and it completes at a principled place rather
than at nothing-left. The audit first: nine `on_write` hooks, one veto, and `answers(<M>, ask)` — the
door built so a **tool's** binding could be data — had **exactly zero apparatus users**. §21's *the
apparatus does not eat its own cooking* was true of every single one.

Six requests, six bindings, all facts now: `<fit>` `<settle>` `<verdict>` `<root>` `<remember>`
`<re-ask>`. Their **bodies stay native**, which is what an answerer *is*; what moved is where the
binding lives, so *which of these exist* is a query. One asymmetry stays and it is the right one: a
tool's answer lands as `answered(<M>, req, y)` for a corpus to believe or not, and an apparatus
answerer writes its answer directly — **a tool is outside the agent, the apparatus is the agent.**

**Deniable is not the same as forgettable, and only two of six are both.**

>**A capability whose absence is the status quo ante is safe to retire.**

| | removed | `-answers(...)` | |
|---|---|---|---|
| `<fit>` | raised | **REFUSED** | standing |
| `<settle>` | 9 failing | **REFUSED** | standing |
| `<verdict>` | 16 failing | **REFUSED** | standing |
| `<remember>` | raised | **REFUSED** | standing |
| `<root>` | raised | obeyed | a corpus may retire it |
| `<re-ask>` | raised | obeyed | a corpus may retire it |

The four are §19's carve-out a **fifth** time, and they carry `standing` — the fact the bundle already
uses for this exact claim, *overridable but not forgettable*. The denial is **refused on the record**,
not ignored, because a denial silently obeyed-or-not is a fourth silent decline.

**`<remember>` was in the safe column first and the measurement moved it.** I argued *narrowing
off means exhaustive recall, which is the default* — wrong about which thing it answers. `_remember`
is not recall's narrowing; it is the **answer to the recall request**, and `<ask-fit>` keys on
`recalled(?r, ?w)`. Measured on a goal reachable only backwards: **15 ticks and two subgoals became 4
and none.** The narrowing is the `prefer` table and the budget. *A criterion is only as good as
knowing what the thing does.*

**And my instrument was wrong the same way twice.** `ugm.bundle` now asks §20's question of
answerers too, in **two columns** because they are two questions. The first version measured *may a
corpus turn it off* by running the whole selftest with the binding denied — which reported every
answerer as costly and meant nothing, because the suite contains checks that merely **inspect** the
bindings. **A mutation instrument can only read a mutation the fixture does not already talk about.**
The same brittleness was in one of my new selftest checks (`refusals == 1`, a global count), and it
made three false anomalies. Also: a removal that makes the runner **raise** now prints `raised`
rather than being folded into `max(1, ...)` — a count there is a lie, since the run stopped at the
first check that could not survive the absence.

**What is left in Python, exactly.** `_dispatch` and `_enter` are not request-answerers at all — the
outbound boundary and the entry to a supposition are **doors, not questions** — and `_forbid`,
`_widen`, `_notice_open` are the three guards §19 argues must not be rules. That is the principled
floor, not a remainder.

**Two of my own checks were wrong and both were traps this repo has already recorded.** A count of
`instances_of(AGAIN)` read **2** where the answer is 1, because the rule's own consequent pattern is an
instance of the relation and holds nothing. And the tool check asked
`answered(oracle, guess(vessel), yes)` — bare — where a tool's name lives in the namespace of
**statements**: `<oracle>`. The twin trap, one namespace along, in a check written after the trap was
written down.

**What it does NOT close:** *when may a binding be reconsidered*, the last of the original four hats.
Re-asking got there because a request is a **proposition** and a proposition can be re-delivered; a
binding is not one, so the same move is not available.

## Latest: **the loop stops rediscovering what it knew**, and a scope can span documents. Commits `delta`, `scopes`.

**The loop was stateless between ticks.** Every tick it re-ran every rule's join over the whole
state, weighed the result, applied one, and threw the rest away -- then did all of it again. Measured
**before** building anything:

| corpus | applications matched | genuinely new | re-derived |
|---|---|---|---|
| 600 facts, 1 join + 1 narrow rule | 5,775 | **75** | 5,700 — **98.7% waste** |
| the kettle fixture | 239 | 17 | 222 — **92.9% waste** |

The second row is the finding. This was never a big-corpus concern: **the agent has been wasting 93%
of its matching since the first tick ever ran.**

**And it needed no new representation.** §4 already says *a moment is a signed delta*, and
`Chain.deposit` already records each entry's position in it -- so *what is new since I last looked* was
always `seat.delta[pos:]`, and the matcher had simply never read it that way. `match` takes a `fresh`
Situation and runs one pass per antecedent member, pivoting on the delta.

| corpus (same fixture both sides) | before | after | |
|---|---|---|---|
| 2,000 facts + 2 rules | 12.7s | **3.1s** | 4.0× |
| 10,000 facts + 2 rules | 905s | **361s** | 2.5× |

Ticks and writes are identical on both sides (207/6,184 and 1,031/265,754), which is the check that
the speed came from not redoing work rather than from doing less of it.

**I first reported this as *did not finish in 600s* → *8.0s*, and both halves were wrong.** The
"did not finish" run was a `python -c` with no tty, so **stdout was block-buffered**: the 2,000-fact
line had been printed and was sitting in the buffer when the command hit its timeout, and I read *no
output* as *did not terminate*. It had finished in 12.7s. Then the "after" number was measured on a
DIFFERENT fixture -- entities mod 300 instead of mod 900, so a denser join -- and compared to it
anyway. Two instrument errors compounding into a headline roughly 20× too flattering.

>**A timeout is not a measurement, and an unflushed buffer is not a silence.** The same lesson the
>runner learned in `bundlefile` (a crash is not a failure) arriving from the output side. Use `-u`.

**Three things had to be right, and I got two wrong first.**

* **Order is part of the answer.** A cache yields applications in discovery order; a full match
  yields them in state order, nested-loop per member. §18's last tiebreak is authored order, so *which*
  application is chosen turns on it -- 4 checks failed. Now reconstructed explicitly.
* **The cursor is PER RULE.** Recall is not fixed: a rule drops out of mind under a budget and
  returns when `_widen` fires. With one shared cursor everything deposited while it was away is already
  consumed, so it comes back and is told nothing is new -- and the chain a→b→c stops at b. *New* means
  new **to this rule**.
* **Invalidation, and it found a hole in the suite.** The chain is append-only but `resolve` is
  **not monotone**: a denial makes what an application consumed no longer the current claim.
  Kill-probed -- disable it and the agent concludes from a premise it has **denied** (`z(a)` = `+` after
  `-p(a)`) -- **and all 316 checks still passed.** Nothing else in the suite could see it.

**What is now the top cost, same disease one layer down:** `current_state` is rebuilt from the whole
chain twice per tick. That is why 5,000 facts still costs 11× what 2,000 does.

## Latest: **a hypothesis can be re-entered**, and the fix was DELETING Python. Commit `reenter`.

The user's case: *explore a hypothesis, find you need something you do not have, go and get it, and
finish the reasoning.* It could not be done.

Measured: explore `broken(pipe)`, want `wet(pipe)`, conclude nothing, discharge -- then be told
`wet(pipe)`, and the hypothesis is **never revisited**, not even when a corpus asks outright. The block
was one line in `_enter` with a reason true only while nothing changes: *supposing the same thing twice
derives nothing new.*

**My first repair was worse, and the user named why: this is reasoning, and it must not be handled
by Python.** I had added a Python test for *was this licensed by `again`* -- the decision back in the
machinery, one layer down. Two kill-probes agreed before the argument did: removing the dedup entirely
failed nothing, and accepting any licence failed nothing.

**Measured instead, and the dedup was REDUNDANT.** Quiescence already stops a rule re-concluding
`suppose(p, w)`, because the proposition already holds. The runaway the old comment feared -- a rule
inside the frame re-supposing its own assumption -- runs **4 ticks to quiescence with the dedup and 4
without, identically.** So both the dedup and my special case are gone, and what decides that a
hypothesis is worth entering again is a corpus writing

    again(suppose(broken(?x), likely), <occasion>)

which is the argument re-asking was already built on, and now the only one. **The fix removed Python
rather than adding it**, which is the sign the user asked for.

**And the re-ask criterion transfers whole.** A corpus that re-supposes on `left(?f, ?a)` -- the
record of leaving a frame -- generates the occasion for the next re-entry *by re-entering*, and never
stops (200 ticks, still going). *An occasion warrants a re-ask only if re-asking cannot produce one*,
in a second place. Not a machinery failure: the criterion is stated and unenforced, and this is an
author writing the `causes`-shaped mistake again.

What is NOT claimed: this does not pause a half-explored hypothesis. A supposition still runs to
quiescence inside and discharges honestly. What it buys is that **finding something out is a reason to
think again** -- re-enter, do not freeze, which is the same answer session resume gave.

## Answered: **mid-plan interrupt, ask, resume — and focus stays a pointer**

The user asked whether treating the focus as data would allow *interrupt planning, ask the user, then
"where were we? oh right, planning", and resume.* Measured end to end, across two processes:

```
1. planned, got stuck, ASKED: ['ask(heated(kettle))'] -> quiescent
2. resumed: re-asked? []          (correct -- it already asked)
   still knows the plan: 2 subgoals
3. answered -> boiling(kettle) = +
```

**It works, and it works because the PLAN is data -- not because the focus is.** *Where were we* is
answered by `goal`, `plan`, `subgoal`, `binds`, `unmet` and `blocked`: ordinary nodes, all restored.
The focus is only the pointer, and holds nothing the plan does not already say.

**And the interesting case cannot arise.** Planning is not a supposition -- backward reading is
ordinary rules at the agent's own frame -- and `_dispatch` refuses to emit inside a hypothesis, so the
agent *cannot* ask a user question while supposing. Every interrupt-to-ask is therefore at the root
frame, where a fresh session already puts the register. Storing focus would buy nothing; where it
would matter is resuming a half-explored hypothesis, and this design does not do that -- a supposition
runs to quiescence inside and then discharges.

**What the scenario DID surface: `achieved` goes stale.** In the first run `boiling(kettle)` was
true in the world and `achieved(boiling(kettle))` was **None** -- the plan's own bookkeeping never
updated, because the `check` was asked once, answered `unmet`, and nothing re-asks. The report is
right (it reads `holds`); the goal machinery is not. That is the re-ask item, demonstrated inside a
real scenario rather than as a hypothetical, and it is now the most concrete thing on the list.

## Latest: **its own effort is reasonable over**. Commit `effort`.

The user's reason, and it is the right one: the counters *should be reasonable over*. An agent that
reached past its shortlist, or was stopped by a bound, knows something about its own effort -- and
that lived in Python counters, so no rule could ask. §21's defect for the seventh time.

    widened(<seat>)     recall reached past its shortlist
    reached(<seat>)     a domain was brought back out of dormancy
    bounded(<which>)    a bound stopped a supposition, and WHICH one

**Events, not counts.** A count cannot be a fact here -- `widened(2)` and `widened(3)` are different
propositions and **both would hold**. §17's pattern was always the right one: deposit the smallest
unarguable record and let rules say what it means, exactly as `quiet`, `left`, `stopped` and `emitted`
do. So the claim is *this happened here*, deduped by reading the graph, and *how often* stays a
question nobody has needed to ask.

**What it buys, in one line a corpus could not write before:**

    rule <patience> = implies( { +widened(?m) }, { +doing(ask(help)) } )

*I had to reach for that -- ask for help.* Measured: the agent emits `ask(help)` under a budget it has
to widen past, and nothing under a budget it does not.

**And it made a false comment true.** `_enter` has said *Bounds, and each reports that it was hit
rather than stopping silently (§13)* since it was written, and the report was `self.exhausted += 1`.
**The code claimed a property it did not have** -- a §5 silence sitting behind a comment denying it.

**Three of five kill-probes were ungated first, and one for an instructive reason.** The dedup
check counted `instances_of`, which returns **propositions** -- three deposits of one proposition are
one node, so a node count cannot see duplication at all and could not fail. Entries, not nodes.
`reached` and the second bound had no fixture. All five bite now.

## Before that: **the knobs are claims**, and the focus is not stored. Commit `knobs`.

Two answers to the same question -- *what state is not in the graph, and should it be?*

**Three knobs became facts**, by the argument `tolerance` was already made a fact for: *how careful
am I being is a claim with a trail, and a rule can raise it before an irreversible step.*

    budget(3)       how many rules recall may propose
    depth(4)        how deep a hypothesis may nest
    hypotheses(5)   how many may be open at once

The DEFAULT stays in Python, exactly as `tolerance`'s zero does. A default nobody has to choose is
not a hidden decision; it is the absence of one. And a denial restores it, because these are ordinary
claims.

**Reading a knob is not obeying it, and the kill-probe found the difference.** With the readers in
place, mutating `depth` and `hypotheses` back to their Python fields failed **nothing** -- the checks
asserted the value came back, never that it steered. The same for the budget, which is read in *two*
places (whether to widen, and how much shortlist to keep) and only the first was covered. All five
sites are gated now, the budget by comparing a corpus-written bound against the Python field it
replaces: with one site unconverted the run widens and never narrows, and the tick counts come apart.

>**A knob that is read and not obeyed is the same defect wearing the fix's clothes.**

### And the focus is NOT stored — measured, not assumed

The user asked whether persistence should record it separately. It should not, and the reason is the
same one that removed the journal: **the focus is derived.** Replaying what the agent was told and
thinking to quiescence reconstructs it. Measured on a session interrupted mid-run:

| | entries |
|---|---|
| lived, interrupted at 12 ticks | 161 |
| resumed | **190** |
| lived, run to quiescence | **190** |

>**A resumed session has finished thinking.** The record says what the agent was *told*, never how
>much it had thought about it -- and thinking further is what it does, not something it was told.

So exact-tick resumption is not offered, and that is a decision rather than an omission: recording
`run(limit)` would be recording an external interruption as though it were part of the session.

## Before that: **there is no journal — the session is RENDERED out of the graph**. Commits `persist`, `rendered`.

The user's question, and it was the right one: *shouldn't the journal be part of the graph? is there
any state that is not within the graph?* The first version of `persist` kept a Python list of
everything that came in. **That was a side-channel duplicating the chain**, in a design whose
thesis is that nothing the machinery knows may be unaskable by a rule -- and a kept list can drift
from the graph, where a rendering cannot. Everything it held was already here:

| the journal held | already in the graph as |
|---|---|
| the corpus text | rules are nodes -- connective, antecedent, consequent all reprint |
| which facts were told | `licence = loaded(p)`, `source = <domain>` |
| what the world said | `arrived(c, p, sign)` entries |
| which scope each was written in | `scoped(<domain>, <scope>)` -- **new**, a claim the loader makes about itself |
| `run(limit)` calls | nothing, and rightly: *think until there is nothing left* is what the agent does, not something it was told |

**What is rendered is a CORPUS, never entries.** §13 scores *authors write entries natively* as a
leak -- supply a deposit and you can date a claim to when it was not held -- so a saved session
replays through the ordinary loading path and earns its stamps again. The save file is the corpus back
out, readable and diffable.

**Two provenance gaps this exposed.** A **rule had no origin at all**: `RuleSet.rules` is a Python
list and nothing said which corpus authored which rule, so reification is now stamped with the
document being read. And a **channel's scope** was unrecorded, so an arrival replayed into a twin that
merely printed the same.

**And a twin trap in the provenance code itself:** `Loader.LOADED` was `g.atom("loaded")` and
`Machine.LOADED` another -- `atom` does not intern -- so the licence the loader stamped and the one
the renderer looked for were two nodes with one name, and rendering found **no told facts at all**.
Sixth time.

**A probe of mine read a crash as clean.** Two mutations (rules not rendered; a sign printed `+`
where the surface reads `plus`) make the save file unparseable, so the suite **raised** instead of
failing and my harness counted zero. That is `bundlefile`'s lesson -- *a runner has to be able to say
False about an absence* -- which `ugm.bundle` was fixed for this morning and my ad-hoc probe
reproduced hours later. The check now catches the `ParseError` and reports False.

### The census: what state is NOT in the graph

Asked directly, and worth keeping. Three buckets:

* **Mirrors of something already in the graph** -- `emitted` (↔ `emitted(x)`; this one caused a real
  bug: a resumed session reported having done nothing), `_acted`, `_quieted`, `_stopped`,
  `_exercised`, `_reified`, `_noticed`, `_vetoed`, `RuleSet.overrides`/`supersedes`. Redundant, not
  hidden. Honest debt.
* **Genuinely privileged, and each with an argument written down** -- `focus` (§4 allows one register
  and says the pointer is the only privileged thing), the substrate objects, the **name tables**
  (which *cannot* be in the graph without making names identity, which §3 refuses), answerer function
  bodies (that is what a tool is), and the caches (derived, re-derivable, gated).
* **Genuinely hidden claims -- the defect pattern, still open.** Counters (`widenings`,
  `recoveries`, `selections`, `matched`, `considered`, `writes`, `refusals`, `exhausted`,
  `expansions`) are facts about the agent's own reasoning no rule can ask about. And **knobs**:
  `recall_budget`, `max_depth`, `supposition_budget` -- while **`tolerance` is a fact**, for the
  explicitly stated reason that *how careful am I being is a claim with a trail, and a rule can raise
  it before an irreversible step*. That argument applies verbatim to the other three. Next commit's
  work, and small.

## Before that: **a session is what it was told**. Commit `persist`.

    python -m ugm <corpus.ugm> --save session.json
    python -m ugm --resume session.json

**Saved as the JOURNAL, not as the object graph** -- corpora loaded, arrivals delivered, runs
asked for. Measured **before** choosing: the same corpus reproduces the same **619 entries byte for
byte across four `PYTHONHASHSEED`s**, so §3's determinism is not an aspiration and *what it was told*
is a complete description of *what it knows*. And unlike a pickle it is a file a person can read, diff
and argue with -- §2's readable criterion, at the one place a save format usually abandons it.

**Replaying a session must not RE-DO it.** The boundary is the one place effects leave and it
cannot tell a repeat from a first time: resume a session that opened a door and the door opens again.
This is `_hypothetical`'s argument in a second place -- *supposing must not bring it about, and
neither must remembering* -- and it needed **no new vocabulary**, because `taken` has always meant
*decided on and not emitted* and the bundle already turns it into `did`.

The two histories differ in exactly one way, which is the design of the whole thing:

| lived | resumed |
|---|---|
| `emitted(open(door))` | **`taken(open(door))`** |
| `exercised(<did>)` | `exercised(<taken>)` |

Same length (126), same order, everything else identical. *The only difference between a lived
session and a resumed one is which record says it acted.*

**Three things the fixtures caught.** The **bundle** was being journalled -- it is not something the
agent was *told*, it is what it reads *with*, and replaying it into a machine that already has it
fails with `<intake> is already declared`. Arrivals lost the **scope** their terms were written in, so
a replay rebuilt twins that merely printed the same; `Loader.say` is now the scoped door for the world
speaking, beside `channel` and `answerer`. And `report` read `self.emitted`, a **Python list of this
process's emissions**, so a resumed session -- which correctly did not act again -- reported having
done nothing. It reads `did(...)` from the graph now. Third time that exact defect has been found.

**The honest limit, stated rather than hidden:** a journal cannot carry a **tool's answers**. An
answerer is a Python function, so a resumed session must re-register its tools -- and a *sampled*
answer would not reproduce at all. §21 already records that a real model needs its seed on the record
before it is reproducible reasoning; this is exactly where that debt comes due.

## Latest: **the agent can say what became of it**. Commit `report`.

§2's not-lossy criterion at the one boundary nobody had crossed. A corpus with a one-character typo
ends `quiescent` with `blocked(water(kettle))` deposited -- **the agent had diagnosed itself exactly**
-- and there was no way to be told. Every `__main__` in this package was an instrument; none was a
door.

    python -m ugm <corpus.ugm> [--limit N] [--why TERM]

```
typo.ugm: 15 ticks, ended quiescent

asked for:
  boiling(kettle)  [open]  via <boil>
    water(kettle)  [BLOCKED]
    heat(?a, kettle)  [open]
```

**A rule now prints as its name.** It is minted as `implies(moment(...), moment(...))` and appeared
that way in every plan node, licence and `unmet` -- ninety characters of its own structure where the
author had written `<boil>`. Names are never identity here, so `Graph.call_it` cannot make two nodes
one; it only gives a node something to print. This is the single largest readability change in the
arc and it is four lines.

**Depth first, left to right -- the user's framing, with their refinement.** `<plan>` and `<expand>`
already built the tree; nothing is recomputed. And: **indent where there is a CHOICE, chain where
there is not.** One way of getting something is not a branch, and indenting it claims a decision was
made where none was -- the same reason `likely(not(p))` reads as one line and not as three.

**Two things the fixtures corrected.** `has_var` is not a filter here: an unbound subgoal
(`heat(?a, kettle)`) is exactly what a reader needs, and filtering it emptied the tree and made
subgoals look like roots. And the walk must NOT descend into the apparatus's own goals -- backward
reading makes `need(...)` and `fits(...)` goals like any other, and shown here they read as things the
user asked for, several permanently `BLOCKED`, which is both true and meaningless.

**`kb.channel(name)`** -- the last twin trap to get a scoped door, beside `Loader.answerer`.
`m.channels.open("user")` mints a socket beside the table the corpus resolves against, so the rule
reading `says(user, ...)` and the world speak on two sockets with one name, silently.

Still absent, and now the honest gap between this and a usable tool: **nothing persists.** Every
session starts from zero, so what `learned()` writes dies with the process.

## Decision: **typing is OFF the list**, and the user's objection is the design's own test

*Types are a superimposed thing, a simplification that risks being wrong.* Agreed, and the case had
already lost two of its three legs:

* **Selectivity — dead.** Typing was to narrow matching by a constant factor. `dormant` over domains
  measured **14.5x** by a mechanism that is an ordinary fact. The constant-factor argument is gone.
* **Act versus state — not a type.** What is actually needed is one narrow question: *can the agent
  bring this about by acting?* In this design that is either an ordinary deniable claim, or -- better
  -- a question about the **boundary**, since what can leave the agent is what an actuator accepts.
  That is anchored, which makes it machinery of the `arrived`/`emitted` family (§17): deposit the
  smallest unarguable record, let rules say what it means. No new kind of thing.
* **Backward termination — the same question, and still open.** The regress walks `doing`/`taken`/
  `did`/`emitted` because nothing says which propositions the agent can bring about. Whatever answers
  the question above answers this too.

**And the objection IS §4's test.** *Adding a connective adds rows, not branches* -- a type system
is a branch, and a checked type is a decision that cannot be argued with, which §2 rules out for
anything admissible. It is also the shape this arc keeps discovering it did not need: the ISA, the
phases, the watchdog registry, a congruence relation for identity.

Nothing currently depends on planning-to-act: every corpus here plans through ground-consequent
rules and works. So this is **optional**, and the open item is one sentence rather than a subsystem:
*what can the agent bring about, and who says so.*

## Latest: **a dry search reaches for what is out of mind**. Commit `escalate`.

§19's carve-out for the **fourth** time, and the argument transfers whole:

>Recall may be incomplete about what to do.
>**It may not be incomplete about what it has NOT looked at.**

`blocked` claims that *nothing* answers a goal -- an aggregate over a **finished** search -- so a goal
whose evidence is merely dormant would be reported unreachable, with the trail showing a completed
search that never ran. Measured, with the escalation disabled and enabled:

| | `chase(acme)` | recoveries |
|---|---|---|
| billing dormant, escalation off | **None** | 0 |
| billing dormant, escalation on | **`+`** | 1 |

**Only when something is OUTSTANDING**, and running it without that condition is how the shape
became clear. The unsoundness is about a **goal**; a run with nothing outstanding declines nothing.
Escalating anyway woke every domain at the end of every run -- **it threw away the entire 14.5x saving
and failed two dormancy checks that were right to fail.** So this carve-out is narrower than
`_widen`'s: *escalate before believing a decline about something I was asked for.*

**And a silent bug the escalation exposed: what is in mind must be part of the MATCH CACHE KEY.**
While a domain is dormant its entries are filtered out of the delta and the per-rule cursors move past
them anyway. Wake the domain and those facts sit behind every cursor forever -- so the escalation
brought billing back and the agent still could not see it. Measured exactly that way before the key
included it.

**A `_widened`-style once-only flag was written first and removed**, because the kill-probe asked
for it: escalating writes `due` for everything hidden, so nothing is out of mind and the next call
returns False -- it terminates on its own. Worse, the flag would BLOCK a legitimate second escalation,
since the only way something becomes hidden again is a corpus claiming it, which is a new decline
about a new dormancy and deserves a fresh reach. **An ungated guard turned out to be a wrong guard.**

Known interaction, not closed: escalation brings the facts back but does **not** re-ask the `check`s
that were answered while the domain was away, so a stale `blocked(<subgoal>)` from the dormant period
survives. That is exactly what `again` was built for, and one corpus rule would do it -- nothing ships
concluding it, in keeping with everything else in the bundle.

**A process note, because it cost work:** mid-way through this commit I ran `git checkout --
ugm/machine.py` to undo a kill-probe that had crashed before restoring, and threw away every
uncommitted edit of the turn. The probe crashed on `cp1252` stdout while printing a check name
containing a star. **A probe that mutates a file must restore it in a `finally`, and must not print
anything it did not encode itself.**

## Latest: **a domain can be taken out of mind**. Commit `domains`.

The user's proposal, and it is the strongest lever measured all session: *load a subset of facts on
demand, unload them when not needed — expert rules decide when.* Their framing, and it needed no new
vocabulary.

**The agent has always narrowed which RULES come to mind — `dormant` until something claims
`due` — and has never narrowed which FACTS do.** Same relation, second kind of thing: rows, not
branches, which is the design's own test that something belongs.

**A domain is a CHANNEL.** §13 already says the knowledge base is one; a named domain refines it
rather than adding a fourth concept. Every loaded fact is stamped with its source, so *which domain is
this from* was already recorded and never read.

| | run | ticks | conclusions in the kept domain |
|---|---|---|---|
| three domains in mind | 22.6s | 600 | 196 |
| **two of them `dormant`** | **1.6s** | 198 | **196 — identical** |

**14.5×, from one corpus line.** It beats both caches built earlier today because it cuts *both*
factors: fewer facts make each tick cheaper AND leave fewer conclusions to draw.

**Out of mind is not untrue, and that distinction is the whole design.** The fact stays in the
chain, stamped with where it came from, on any trail that used it — `holds` answers and `why` would.
Dormancy takes **attention**, never the record. Unloading from the chain would break §12's weakest link
and put `why()` in the dark, which is the one thing this may not cost. My first check asserted the
unloaded fact was gone; the check was wrong, not the code.

**Sharing NAMES and sharing PROVENANCE are different things**, and tying them together was the
first version. Rules about billing must resolve `owes` to the node the billing facts use — one *scope*
— while not being billing data, or unloading billing unloads the rules that read it. So a document
declares `scope` and `domain` separately, `domain` defaulting to `scope`. Caught by the first fixture
that needed both, which produced 2 ticks and 0 conclusions.

**Four filter sites, and the kill-probe found three of them ungated in turn.** Filtering the kept
state left the *matching delta* unfiltered, so a dormant fact was invisible to the state and still
matched once on the tick it arrived. Then the state's own filter was unreachable until a fixture used
a **two-member rule**: with one member the dormant fact is always the pivot, so the delta filter
already excludes it, and only a join draws the other member from the full state. Each of the four now
fails its own mutation.

>**A fixture can only see a filter that its rules can reach.** One antecedent member hid an entire
>code path from a suite of 333 checks.

**Not built, and it is §19's other half:** unloading is safe to be wrong about (worst case the domain
comes back), which is exactly why it may be an ordinary defeasible rule. The **escalation** — reaching
for a domain when the search comes up dry — may *not* be, because a goal whose evidence is merely out
of mind would read as `blocked`, an aggregate over a search that never happened. Same shape as
`_widen`, arriving from a fourth side, and it is the next thing this needs.

## ...and then the walk itself: **the state is kept, not rebuilt**. Commit `state`.

With matching out of the way, §4's walk was the binding constraint -- `current_state` collects every
proposition the chain has ever claimed on this branch and `resolve`s each, and it ran **twice a tick**.
The same observation fixes it: a moment is a delta, so the state after a write is the state before plus
one claim. What is kept is `proposition -> (key, entry)` where the key is `resolve`'s **own** ordering
(locus depth, deposit depth, position), so a later claim replaces an earlier one exactly when `resolve`
would have preferred it. Nothing re-derives the ordering; it reuses it.

| corpus (same fixture throughout) | baseline | after `delta` | after `state` | |
|---|---|---|---|---|
| 2,000 facts + 2 rules | 12.7s | 3.1s | **1.5s** | 8.3× |
| 10,000 facts + 2 rules | 905s | 361s | **74.7s** | 12.1× |

Ticks and writes are identical at every step (207/6,184 and 1,031/265,754), which is the check that the
speed came from not redoing work rather than from doing less of it.

**Order is semantics here, more sharply than in matching.** `current_state` returns propositions
**most-recently-claimed first**, and §18's *a description with two candidates resolves to the most
recent* rests on it. An updated proposition is therefore re-inserted at the end of the dict and the
result read back reversed, reproducing the walk exactly.

**And the kill-probe is the finding: THREE of four mutations changed nothing 323 checks could
see.** Only the ordering one was caught. The three that were invisible -- not re-inserting on update,
letting a later deposit about an earlier locus win, and dropping the locus filter -- are each a place
where an incremental state silently stops reproducing `resolve`. All three now have checks, and each
mutation fails exactly its own.

>**An optimisation of a read is a re-implementation of its semantics.** `resolve` had one
>implementation and now has two, and only the suite says they agree.

## ...and: **a scope can span documents**. Commit `scopes`.

The user's question, and it reframed coreference entirely: *could explicit bounded references avoid
solving coreference, except at intake?* **Yes -- and it was already the architecture, more strictly
than anyone had written down.** Measured: each `load()` is its own name table, so `kettle` in two
documents is two nodes and neither sees the other's claims. Engine vocabulary is shared (`m.reserved`);
user names are not.

>**Within authored knowledge, coreference is not solved -- it is ABSENT.** A corpus is a bound, and
>inside it `kettle` means one node by construction. The twin trap that has cost this repo five silent
>bugs is the design enforcing exactly that: a name not resolved through a scope names nothing.

**And it settles the interning question.** I had framed it as a trade -- interning is irrevocable
coreference, minting a node per mention is revisable but leaks. With bounded references the dilemma
dissolves: **within a bound, interning is correct**, because the bound is what makes it a fact rather
than a guess. No node per mention, no leak.

What it cost was that a book split into chapters was that many disconnected islands. So scopes are now
**named**: `load(m, src, scope="book")` shares one table; omitted, the document is private, which is
the default and unchanged. A rule authored in one document now applies to facts in another. Gated with
a control (an unscoped document stays apart) and kill-probed.

**What this deliberately is NOT: `sameas(a, b)` in the graph.** Asserting identity needs
equals-for-equals in matching, and congruence is either machinery -- a decision nobody can argue with
-- or a rule per relation per position. **Deciding identity where the name is READ keeps it a
construction.** Identity discovered later is then a **revision of intake** (re-read the document with
the binding corrected), which is the shape `learned()` already has for rules.

**Three residues, stated because they are real.** Choosing the bound is itself a coreference
judgement made **wholesale** -- one scope per book says chapter 2's kettle is chapter 40's, decided by
how the file was split rather than by evidence, and that is a claim about the text. Cross-scope
identity is now expressible by *sharing a scope*, never by asserting it. And **binding during
reasoning** -- `binds(plan, ?t, sink)`, *which tap* -- is untouched: that is reference as BINDING, and
nothing reconsiders one. Still the last open hat.

## Survey: **what the two consumers would need, and the wall is scale**

**First, a fact nobody had written down: `../pystrider` and `../harneskills_new` are dark right
now, and silently.** `universal-graph-machine` is **editable-installed pointing at this working tree**,
so whichever branch `ugm` is checked out on is what both siblings import. On `restart`,
`import pystrider` fails at once (`cannot import name 'access' from 'ugm'`). They import ~20 modules —
`world_model`, `cnl.*`, `isa`, `production_rule`, `lowering`, `asm`, `driver`, `goal`, `norm`,
`execution`, `thread` — and `restart` shares **not one name** with them. Also `restart` calls itself
`0.4.0` of the same distribution `main` calls `0.3.0`, and `harneskills_new` pins `>=0.3.0`, so an
ordinary upgrade would hand it an engine with no overlapping API.

**The user's call (2026-08-12): leave them; finish the engine first.** Recorded here so it is a
decision and not a surprise. The cheap decoupling, if it is ever wanted, is a worktree of `main` at a
fixed path plus repointing the editable install, and renaming this distribution.

**What they actually ask of an engine**, read off their call sites rather than their prose:

| they call | the new floor |
|---|---|
| `run_rules(graph, bank)` — saturate a bank, batch | `m.run()` to quiescence — but **one application per tick**, arbitrated |
| `ask(s, p, o)`, `explain(s, p, o)` | `m.holds(...)`, `m.why(...)` — better, the trail is load-bearing |
| tool registry (`tools=registry`) | `answers(<M>, ask)` — better, the binding is **data** |
| `stratify(rules)` | stratum 0, and *the last stage must be total* is the same condition |
| deontic `forbidden` / `forbidden_for` | `forbidden(<pattern>)` + the gate veto — consulted at the write |
| plan → act → check → replan | backward reading, `doing`, `check`/`achieved`, and §19's guards |
| `graph.nodes_named(...)`, `graph.name(n)` | ⛔ **refused by design** — names are not identity |
| `graph.remove_node(...)` (teardown, 6 sites) | ⛔ **refused by design** — the chain is append-only; denial is a `-` entry |
| `run_rules(..., provenance=False)` | ⛔ **refused by design** — R5 licenses every entry; there is no off |

**The three refusals are the design working, not gaps** — each is a decision `rules-design.md`
argues for. But note what the third and fourth cost a real consumer: harneskills' **replan** loop is
`TEARDOWN_RULES` with provenance off, i.e. *undo what the last plan asserted and try again*. On this
floor that is **exactly the two items still open** — nothing retracts a conclusion whose support was
withdrawn, and *when may a binding be reconsidered*. The consumer's most ordinary loop lands precisely
on the arc's last unsolved hat, which is worth knowing before anyone calls those items academic.

**And the wall is SCALE, measured rather than assumed.** One rule, a chain of `edge` facts —
**and see `weigh` at the top of this file: this fixture is the WORST case, not a typical one.**
99.6% of its candidates genuinely apply, against 10.6% across the selftest suite. The quadratic is
real; this benchmark maximises the one axis that produces it.

| facts | run | ticks |
|---|---|---|
| 200 | 0.8s | 202 |
| 1,000 | **21s** | 1,002 |
| 4,000 | **345s** | 4,002 |

**Quadratic** — 5x the facts costs 26x the time. harneskills folds a **code property graph** into facts
and has a `bench/cpg_scaling.py` for exactly this; real code graphs start at thousands of nodes, where
this floor needs six minutes.

**And the cause is not what I first said.** I inferred *a whole-state read per tick*. Profiled, that
is 17%: the cost is **`_would_change`, 38% of runtime and 641,600 calls across 802 ticks** — ~800 per
tick. Every tick the loop **re-derives every applicable instance and re-tests each against the chain**,
then discards the ones it already did.

>**The agent recomputes its entire option set on every move.** Nothing remembers that an application
>was already made, so quiescence is paid per candidate per tick.

**Half-closed 08-13 by commit `quiet`** — the verdict is remembered, which is 2× and leaves the
quadratic exactly where it was. The sentence above is right about the waste and wrong about the
cause: *paid per candidate per tick* made it sound like the per-candidate cost was the problem. The
candidate **list** is the problem, and it grows with the corpus. See the top of this file.

That is the same shape as §14's index finding from the other side — the earlier win was *narrowing what
comes to mind*, and this is *not re-deriving what has already been done*. It is also why the honest
scope line stays **session-sized**: not a slow implementation of the right loop, but a loop whose cost
is quadratic in what the agent knows.

## Before that: **a root goal is askable**. Commit `rooted`.

§6 recorded *a root goal is never checked for satisfaction*; §12 recorded why it could not be a rule.
*A root goal is a `goal(?w)` with **no** `subgoal(?p, ?w)`* is a **negative existential**, and a `−`
member says *an entry denies this*, never *for no `?p`*. That is the same shape as `blocked` — so it
gets the same treatment, which is the point of having settled it once:

    root(w)        a REQUEST, asked by a corpus rule
    rooted(w)      the answer, deposited only when it IS one

**It answers only yes.** A machinery that answered *no* would be asserting a negative existential of its
own; §17's rule is the smallest unarguable record.

**What it unblocks is one line no corpus could write before:**

    rule <done> = implies( { +goal(?w), +rooted(?w), +?w }, { +enough(?w) } )

*What I was **asked** for holds, so I am done.* A satisficing agent's whole policy, generic, over any
corpus. And `ugm.workload` can finally measure the thing it has been apologising for since it was
written — its stop rule was authored **ground**, naming the very proposition the goal is:

| D=8 R=8, stop rule | →goal | →end | how |
|---|---|---|---|
| none | 57 | 124 | quiescent |
| authored **ground** (the old ceiling) | 57 | 59 | stopped |
| **general, via `rooted`** | 66 | **68** | stopped |

Nine ticks dearer than the ceiling, and it **stops naming the answer** — which is what the file's own
caveat says was wrong with it. Gated both ways.

**A correction to my own expectation.** I predicted the version *without* `rooted` would stop early on
a satisfied subgoal, as the `stopping` measurement recorded (tick 51 of a 57-tick run). In the small
kettle fixture it does **not** — it ends `quiescent`, because the `openloop` veto catches it first: an
open goal outranks `enough`. So the veto masks the unsoundness at small scale, and the check is written
around what was actually measured (a subgoal that **holds** is still not `rooted`) rather than around
what I expected to see. Kill-probed: make the answerer say yes unconditionally and two checks fail.

**Blocked on this, now unblocked:** the general stop rule (done, above) and §6's own item.

**And what it does NOT unblock, which is the finding.** Root-goal *satisfaction* checking needs one
more thing, and it is **not** rootedness. With `rooted` in hand a corpus can ask — `{+goal(?w),
+rooted(?w)} ⟹ {+check(?w, ?w)}`, the goal as its own plan, needing **no engine change** because a root
goal binds nothing — and the whole chain fires: `root`, `rooted`, `check`. `achieved` still does not
appear. Measured as a contrast pair whose two cases differ only in *when* the goal became true:

| | goal holds | `achieved` |
|---|---|---|
| goal holds from the start | `+` | **`+`** |
| goal derived a few ticks later | `+` | **None** |

The blocker is §6's *other* item: **a request can only be made once.** The check is asked the moment the
goal appears, the state is scanned then, and re-concluding `+check(w, w)` changes nothing, so quiescence
drops it. A goal satisfied three ticks later is never looked at again.

>**`rooted` was necessary and is not sufficient.** What is left is *when may a request be re-asked* —
>one of the two original four hats, and now the single thing standing between the agent and noticing
>both its own satisfied goals and its own dead rules.

## Before that: **a rule says that it ran**. Commit `exercised`.

The user's framing, and it reframed the whole watchdog question: *dying is searching for a rule and
finding none, isn't it?* Yes — which means the machinery for noticing a dead rule **already exists**
(`<give-up>` asks a verdict at `quiet`, `blocked` says no rule fits, §19's veto refuses to end quietly
on an open goal), and the only addition is **being able to die on it**. No census, no watchdog registry,
no pairing each rule with a guard — all of which I had proposed one message earlier.

    exercised(<R>)      that this rule has run — a PROPOSITION, not a licence

**The third thing found in this shape, and all three close the same way.** `applied(<R>)` has been
on every derived entry since R5, because §12's weakest link needs it — and unreadable, because a licence
is a Python field on the entry. Same as an entry's **grade** (§21 item 5, closed by a wrapper) and a
**tool's binding** (closed by `answers(<M>, ask)`). *Something the machinery knows and no rule can ask
about* is this codebase's most frequent defect, and the fix is always: put it in the graph.

Deposited **once per rule**, deduped like `reify` — it is a claim about the rule, not a count of its
applications. Kill-probed: remove the deposit and the check fails.

**The reaction half is NOT here, and the blocker is §6's rather than a new one.**
`blocked(exercised(<R>))` is written **whether or not the rule ran**, because `blocked` means *no RULE
fits this* — true either way, since what concludes `exercised` is the machinery. The discriminator would
be `achieved`, and §6 already records that **a root goal is never checked for satisfaction**:
`<ask-check>` keys on `subgoal(plan, ?w)`, and a goal with no plan is not expressible. Measured, both
ways, and recorded as a check.

So: the half that is sound ships; the half that needs the root-goal check waits on an item that was
already on the list, and is now the thing standing between the agent and noticing its own dead rules.

## Before that: **bagging does not pay — summation is not voting**. Commit `forest`.

`forest(episodes, cost)` — bag the episodes into deterministic slices (§3: unseeded bags would be the
read-a-result-out-of-a-set bug wearing a hat), grow a tree from each, emit them all. Measured on the
situation-dependent fixture: **one tree 1, forest 2, nothing 4.** It is *worse*, and the reason
falsifies the claim it was built on — recorded rather than quietly fixed.

>**`_priority` SUMS, and summation is not VOTING.** In a classifier forest a minority tree is outvoted.
>Here every tree's rows are **added**, so one bag that pruned to an unconditional `prefer` fires in
>every situation and **cannot be outvoted** by the two trees that learned the condition. The ensemble
>has a way for advice to accumulate and no way for it to be overruled.

**CORRECTED 08-13, and the last sentence was wrong.** Probed directly: `_priority` resolves each
row through the chain and requires `+`, so **a `prefer` row is an ordinary deniable claim** —
`-prefer(<byB>, at(p), 5)` restores the loser, and so does a `standing` rule concluding the denial.
The overrule mechanism was there all along; the forest experiment never reached for it.

**And the real defect is one layer down, in R7 rather than in the combination rule.** Measured:

| | first move |
|---|---|
| `B:5` vs `A:3` **and** `A:3` (the same row twice) | `byB` — 3+3 = **3** |
| `B:5` vs `A:3` **and** `A:4` (distinct rows) | `byA` — 3+4 = 7 |

Two identical rows are **one proposition**, because propositions intern. So:

>**An ensemble's agreement is invisible and only its disagreement adds.** Two trees that learned
>the same row contribute once; two that learned different scores for the same rule accumulate.

That is a sharper reason bagging failed than *summation is not voting*, and it is a **representation**
fact rather than a policy choice — which is why `_priority`'s summation is left alone.

**And it was already written down, in the other file, about the other question.** `ugm.learning`
has said since `induce` that *a second `prefer` row for the same rule and key does not accumulate —
restating is not revising (§8)*, filed as a limit on **frequency** (nothing weighs a route that
usually works against one that worked once) and closing with *that is the next thing to measure, not
to assume*. Nobody joined it to `forest`'s verdict two commits later. **The same property was a known
limitation in one file and an unexplained failure in another**, and what closed the gap was measuring
the note rather than re-deriving the verdict.

I claimed the opposite two commits earlier — *combination is already the mechanism, a set of shallow
rules is a forest natively*. Summation makes an ensemble; it does not make **bagging** sound.

The unanimity test built to hedge disagreement is also too coarse: the trees all advise the same
**rule** and disagree about *when*, so nothing was hedged. **Agreement has to be about the condition,
not the conclusion** — the same lesson `refine` and `induce` each learned, that the structure is in the
antecedent. What a forest needs here is a combination rule that can **defeat** rather than only add;
§12's `overrides` is the obvious candidate and is untried.

**And a regression I shipped: the `magnitude` commit's line-splice DELETED ten gates** — the whole
decision-tree and induction block — and nothing noticed, because a gate count only ever appeared in
prose. Restored from `induce`; the instrument reports **31** gates. *An instrument that cannot say how
many checks it ran cannot tell you it stopped running some.*

## Before that: **how sure is a WRAPPER, not a field**. Commit `hedge`.

**The handoff's previous paragraph was wrong and the user caught it.** It said the *how sure* half
was waiting on `+prefer(<R>, k, 3) @possible`, "already writable and never written". Measured: the grade
parses, lands on the entry — and `_priority` **never reads it** (3 with `@possible`, 3 without). So it
was writable *and unreadable*, which is not a channel. Worse, reading `e.grade` there would have deepened
§21's item 5 rather than fixed it: **grades are Python fields on the entry, so no rule can read one.**

The user's correction: *we argued they could just be wrappers, with a rule crossing it and receiving the
result afterwards.* Right, and it needs **nothing built**:

| in the corpus | `_priority` | acts |
|---|---|---|
| `prefer(<use-b>, goal, 3)` | 3 | `b` |
| `+possible(prefer(<use-b>, goal, 3))` | **0** | `a` |
| ...plus a rule taking it up when `+exploring` | 3 | `b` |
| the same rule, not exploring | 0 | `a` |

**An unsure preference must not silently steer, and a wrapper is exactly that.** It is an ordinary
node, so `_priority` does not count it and a *rule* decides whether to:

    rule <venture> = implies( { +possible(prefer(?r, ?k, ?n)), +exploring },
                              { +prefer(?r, ?k, ?n) } )

**So explore/exploit stops being machinery and becomes a CLAIM** — defeasible, deniable, on the
trail, switched by an ordinary fact. `induce(hedge=True)` emits the wrapper for a route it has never
observed. From a bad start:

| | losses per episode |
|---|---|
| unhedged | 2, 1, 1, 1 |
| **hedged, no explore rule** | **2, 2, 2, 2** — never ventures |
| hedged + `<venture>` | 2, 1, 1, 1 |

The conservative default is now *exploit*, and venturing is something a corpus says out loud. And the
test is **constant-free**, which §15 went to trouble for: *observed* versus *never tried* is a
distinction the trail makes, not a threshold anybody chose.

Note what this makes of §21's item 5. *Grades are not in the graph* stops being a blocker for
learning — not by putting them there, but by showing the quantity that needed reading was never a grade.

## Before that: **magnitude — and it needed no negative numeral**. Commit `magnitude`.

§21 carried *how badly a rule cost something is unsayable* as **blocked on the table's numerals being
non-negative**, and it was pickup item 1 for four commits. The blocker dissolves once the quantity is
named correctly:

>**Harm is HOW MANY WANTED THINGS WERE LOST. That is a count, and a count is non-negative.** Nothing
>ever has to say `-3`; the comparison that matters is *this route cost two and that one cost one*.

`blame()` now deposits `harmed(<R>, key, n)`, and `harm_of(rule)` totals it. The magnitude is an
aggregate over everything lost, so it is deposited **after** the walk — writing it inside the loop would
report the first count as the answer, §16's ordering trap in a smaller place. And `induce()` accumulates
observed harm across episodes, scoring a route `base + worst − its own cost`.

| start | before | **now** |
|---|---|---|
| good (jug first) | 1, 2, 1, 2 — oscillates, degrades | **1, 1, 1, 1** |
| bad (vase first) | 2, 1, 2, 1 — oscillates | **2, 1, 1, 1** |

    fact prefer(<use-jug>, water, 4)      base 3 + worst 2 − own 1

**The lesser evil wins by exactly its margin**, and both starts converge. From a bad start it pays the
costly route **once** and then stays — which is right: that is what buying the knowledge costs.

**A route never tried scores full**, so ignorance reads as **optimism**. That is what still makes the
agent explore rather than settle on the first thing that merely worked — the failure mode the
hand-authored magnitude ceiling had (`2, 2, 2, 2` forever).

**Five gates asserting the oscillation failed when this landed — that is them working.** They were
labelled *passes on today's wrong behaviour, so the day it changes they fail and send someone to the
argument*. Third time that pattern has paid in this arc. Rewritten as guarantees.

**What is still missing is the SECOND quantity, and it is now the only thing.** The score says *how
good*; nothing says *how sure*. §10's ordinal grade on the entry is the place for it —
`+prefer(<R>, k, 3) @possible` is already writable and never written. Until then exploration is paid in
full every time: nothing lets the agent be less sure of a route it has tried once than of one it has
tried twenty times. **That is exactly the pair a forest yields natively — score from the mean, grade
from the spread.**

## Before that: **a tree with more than one leaf**. Commit `induce`.

`induce(episodes, cost)` — several episodes each propose a leaf (*the alternative I wish I had taken,
conditioned on what was true when it went wrong*), then the leaves are pruned **jointly**. Leaves cross
episode boundaries as **text**, not nodes, because episodes are separate agents with separate graphs —
§3's *names are not identity* deciding an interface, and the same one `learned()` already had.

    leaves proposed 3, unconditional among them 2, kept 1
    rule <learned-0-use-tap-water> = implies( { +precious(?v0) },
                                              { +prefer(<use-tap>, water, 3) } )

**Wrong leaves are expected, and pruning is what makes that safe.** An episode only ever knows the
cost of the route it **actually took**, so an episode that broke a jug proposes *prefer the tap* whether
or not the tap is worse — which is exactly the oscillation `lesser_of_two_evils` measures, arriving here
as an ordinary **over-general hypothesis**. Two of the three proposals were unconditional and wrong;
joint pruning dropped both and reached the same optimum as the hand-refined single rule (total **1** vs
depth-0's 2). **The oscillation stops needing its own mechanism.**

**Order matters on a plateau, and the first version collapsed because of it.** Reaching the good
tree needs **two edits** — drop the unconditional leaf *and* drop a test — each individually neutral. A
greedy walk that accepts ties goes wherever trial order sends it, and mine dropped the **good** leaf and
collapsed to the very unconditional row it was meant to beat. Ties now doubt the **least specific leaf
first**, which is not a knob: *a leaf with no tests fires in every situation, so it is the strongest
claim in the tree and the first that should have to earn its place.*

That is the second time in two commits that the search's **tie-handling**, not its objective, decided
whether learning worked at all. Worth remembering before any forest: the fitness was never the hard part.

## Before that: **refinement — the tree finds its own depth**. Commit `refine`.

`Machine.refine(cost)` — reduced-error pruning over corpus text, greedy backward elimination against a
`cost` the caller supplies (it must: what an episode cost is a question about a world, and this object
is not one). Third situation added to the fixture — **C is A without the set**: precious, completing
nothing, which is what makes *over*-specific advice measurably wrong.

| carried forward | A | B | C | **total** |
|---|---|---|---|---|
| nothing | 2 | 1 | 1 | 4 |
| depth-0 (an unconditional fact) | 0 | **2** | 0 | 2 |
| depth-2 (every circumstance) | 0 | 1 | **1** | 2 |
| **refined (depth-1)** | 0 | 1 | 0 | **1** |

    rule <learned-use-tap-water> = implies( { +precious(?v0) },
                                            { +prefer(<use-tap>, water, 3) } )

*When something is precious, prefer the tap.* **Both too-shallow and too-deep are worse**, so the
optimum is interior and the search has something to find. §4's *compose what never surprised* from the
other end: **decompose what turns out not to matter.**

**STEEPEST descent, not first-improvement, and it decides whether this works at all.** My first
version took the first drop that tied — and pruned the tree to **nothing**, arriving back at the
unconditional row it was supposed to improve on. `{precious, completes}` dropped `precious` for an equal
score, then dropped `completes` for an equal score; dropping `completes` **first** scores strictly better
and is the answer.

>**A tie is not evidence that a test is worthless. It is evidence that THIS drop is neutral, and
>another may not be.**

Kill-probed: restore first-improvement and two gates fail. Ties still go to the **more general** rule
(`<=`), which is the only judgement in the method — between two hypotheses that explain the evidence
equally, fewer conditions transfer further.

Still not mutation: it only *removes* a test it already had. It cannot add one it never saw, merge two
rules, or revisit a tree that has stopped paying. §21.

## Before that: **a learned rule IS a decision tree**. Commit `trees`.

The user: *decision trees to choose the rules; this could also help generalisation, by mutating decision
trees of rules — we have to think the best "learnable" shape given our system.* The answer turned out to
be that **the shape was already here**, and three properties of it were true and unnoticed.

**A tree's root-to-leaf path IS a rule.** Antecedent = the conjunction of tests, consequent =
`prefer(<R>, key, score)`. Not an analogy — the same object, and `<relevant>` has shipped in exactly
this shape since §13. **A `prefer` FACT is a decision tree of depth ZERO**: it says *always*, given its
key. A rule says *when*.

**`_priority` SUMS applicable rows, so preference is already an ADDITIVE ENSEMBLE.** Measured at
4 + 3 = 7. A set of shallow learned rules is a forest *natively* — nobody designed it as one; it falls
out of *applicable rows sum*.

**Generalising is unconstrained, and that is a property of the shape.** A preference consequent
holds **no variables**, so the loader's rule that consequent variables must be bound is satisfied by
anything. A rule concluding about the *world* would not have that freedom. This is why preference is the
learnable seam and conclusions are not — the third distinct reason for the same line.

`learned(conditional=True)` now emits a rule instead of a fact. Taught by one episode:

    rule <learned-use-tap-water> = implies( { +completes(?v0, ?v1), +precious(?v0) },
                                            { +prefer(<use-tap>, water, 3) } )
    fact standing(<learned-use-tap-water>)

*When something precious completes a set, prefer the tap* — generalised over the objects it saw, and it
correctly **declines to fire** where the tap is the expensive option. Measured on two situations that
share a goal relation and disagree about the right move:

| carried forward | situation A | situation B | **total cost** |
|---|---|---|---|
| nothing | 2 | 1 | 3 |
| depth-0 (an unconditional fact) | 0 | **2** | 2 |
| **depth-1 (a learned rule)** | 0 | 1 | **1** |

The depth-0 row fixes the world it learned in and is **wrong in the other**, which is the point of the
fixture: one unconditional row cannot express *when*.

**The tests come off the trail, so the hypothesis space is the corpus's own vocabulary** — no feature
engineering. `_circumstances` takes the ground propositions on the support of what was **lost**, less
four kinds that cannot discriminate (the lost goals, machinery bookkeeping, what the **choosing** rule's
antecedent already requires, anything generic). Sixth time R5's trail has supplied a learning signal
with no new bookkeeping.

**`standing` is load-bearing and the fixture found it.** Unmarked, a learned preference rule mentions
`goal(?w)`, so forgoing reads it as *a rival way of getting the same want* and passes it up before it can
advise — measured, `forgone(<t1>)` deposited and priority **0**; marked, priority **7**. It is also right
on the merits (§16: *being careful has to come before the move it is about*). Kill-probed: drop the line
and two gates fail.

**A bug that looked like a decision.** The first `_circumstances` excluded the antecedents of *every*
blamed rule — but blame reaches the **physics** (`<cost>`, `<extra>`), and the physics rules are exactly
the ones naming the damaging circumstance. So it learned nothing and looked like it had merely declined
to. Only the **choosing** rule's antecedent may be excluded (`_choosers`: a rule that licensed a
`forgone` deposit is one that was picked over something else). Kill-probed: restore it and 3 gates fail.

**What is NOT here: refinement.** One test-set, all of it, chosen on which error is recoverable —
over-specific advice does not fire and the agent falls back; over-general advice is confident where it
has never been. Nothing prunes a test that turns out not to matter, merges two rules, or revisits a tree
that stops paying. **That is where mutation goes** — and it is affordable exactly because a learned rule
concludes `prefer` and never `doing`: a bad candidate costs ticks, not jugs. Evolutionary search over an
acting agent would be ruinous; over an advising one it is cheap.

## Before that: **the lesser of two evils, and the two open items are ONE**. Commit `evils`.

The user's proposal, and it is a better one than mine: *machine learning could earn its keep on
**gradable quantities** — a random forest to decide the rule.* Right, and for a reason the design says
out loud. It is full of numbers nobody can justify — `tolerance(2)`, `prefer(<R>, key, 3)`,
`<relevant>`'s flat 1, every authored `@likely` — and §15 went **ordinal specifically to dodge them**
(*"close would need a threshold constant nobody could justify"*). That is a design accommodating the
absence of a learner. And unlike recall, **there is no exact algorithm here**, which is the test the
`advisor` measurement just established.

Measured before building. A world with **no safe route**: two ways to water, both destructive, one
twice as costly (the vase completes a set, so shattering it loses two subgoals).

| authored first | today's scheme | ceiling: magnitude, accumulated |
|---|---|---|
| jug — the **better** route | **1, 2, 1, 2** | 1, 1, 1, 1 |
| vase — the worse route | 2, 1, 2, 1 | **2, 2, 2, 2** |

**Today's scheme oscillates, and from a good start it makes the agent WORSE.** `learned()`
suppresses whatever harmed and promotes whatever was passed up — with no notion of *how much*, so it
alternates forever, and from the better route it learns its way onto the costlier one. Learning is
doing nothing here except taking turns.

**And magnitude alone does not fix it.** The ceiling records what each route actually cost and
accumulates across episodes. It converges immediately — **on whatever it tried first.** Better from a
good start, permanently worse from a bad one.

>**Neither is learning. One explores with no memory; the other remembers with no exploration.**

**So pickup items 1 and 2 are the same item, and what is missing is a SECOND QUANTITY.** Both
scales already exist and are already kept apart on purpose (`doubt-is-a-tie`): a **cardinal score on the
table** for *how good*, and **§10's ordinal grade on the entry** for *how sure*. `+prefer(<R>, k, 3)
@possible` — *a strong recommendation the agent is not certain of* — is exactly the sentence
explore/exploit needs, it is already writable, and **nothing writes it from experience.**

**That is precisely where a forest earns its keep**, and it is a fit rather than a gesture: a forest
yields a prediction **and a spread across trees** — a value together with a confidence, which is the
pair the design wants and cannot currently produce. Score from the mean, grade from the spread.

Built into `ugm.learning` as `lesser_of_two_evils()`, with **four gates that pass on today's wrong
behaviour on purpose** — the pattern that has already paid twice this arc (six gap checks failed the day
forgoing landed and sent someone to the argument).

**What the build order has to be, and the forest is not first:** the numerals are non-negative and a
numeral is an atom whose *name* reads as a number, so `-3` is unsayable — the representation must carry
magnitude and accumulate before any learner has an output vocabulary to aim at. Then the pair
(score, grade) written from the trail. Then, and only then, a forest to **generalise magnitude to routes
never tried**, so the agent need not shatter a vase to learn that vases are precious.

## Before that: **an advisor at recall can only lose**. Commit `advisor`.

The user picked recall as the place to put the first model. Measured before wiring one, because §19's
whole argument for putting learning there is *being wrong there is recoverable* — and a model is wrong
by construction, so that claim is load-bearing and had never been tested. It is **true and insufficient**,
and the measurement says do not put a model here at all.

| D (domains the agent knows) | no table | **ideal** table | confidently wrong |
|---|---|---|---|
| 6 | 43 | 43 | 103 |
| 12 | 43 | 43 | 175 |
| 24 | 43 | 43 | **319** |

>**An advisor at this seam can only lose.** A perfect table buys exactly nothing at every scale; a
>confident wrong one costs 2.4×, 4.1×, 7.4× **as the agent's knowledge grows**. The risk scales with
>what it knows and the prize does not exist.

**Why the prize is zero, and it is not §13's blocker alone.** `->goal` is **43 at D=6, D=12 and
D=24** — it does not move with the agent's knowledge *at all*. The agent is **already perfectly
selective**, because §14's `by_conclusion` index answers *what could produce this* **exactly**. A model
here would spend inference approximating something an index computes precisely.

>**Put a model where there is no exact algorithm, not where there is one.** Intake (prose →
>propositions, measured at 0/50) and grounding (`achieves(a, w)`, hand-authored today) are seams with
>no algorithm at all. Recall is not one — and the criteria table I scored earlier got this wrong
>because it asked *is it safe to be wrong here* and never asked *is there anything to win*.

**And the control turned a cost result into a SOUNDNESS one.** Disable `_widen` and a confidently
wrong advisor does not merely slow the agent: the goal is **never reached**, and the run ends
`quiescent` — *nothing left to do* — at tick 52. The agent does not fail. It reports having nothing to
do while the thing it wanted is unreached.

§19 argued *a shortlist that ran dry is not a search that finished* about a **budget too small to reach
a rule that was there**. A bad advisor is the same error **with an author**, and the same one line
answers both — the guard arriving from a third side, having been designed against neither.

>**A model at this seam is safe exactly to the extent that `_widen` is, and not one step further.**

Being wrong *is* recoverable, exactly as §19 claimed, and the widening counts are the guard firing
(30, 66, 138). But **recoverable is not free**, and nothing in §19 ever said what recovery costs.

Built into `ugm.workload` as `fallible_advisor()`, with two gates that pass on **today's** behaviour on
purpose: if an ideal table ever moves time-to-goal, §13's blocker is fixed and recall is measurable
again; if bad advice stops costing more as the agent knows more, something else changed. Either failure
sends the next person to this argument.

## Before that: **a tool is data**. Commit `tools`.

The user asked whether to start leveraging tools, whether some could be small models doing what rules
genuinely cannot, and whether the two halves could be **jointly trained**. Their call on where to cut
in: *the seam first, no model yet* — close §21's debt so a tool is data like the bundle now is, with a
stub answerer standing in for the model.

**A tool is not a new kind of thing, and the architecture was already here.** `_fit` and
`_verdict` are requests **answered by a function rather than by a search** — stratum 0's escape from
§5's wall, and the only shape something outside the agent can honestly take. What was wrong was never
the shape; it was that the *binding* was a Python line, so a corpus could not ask which tools existed,
retire one, or reason about one. Two ordinary relations close it, no new primitive:

    answers(<M>, ask)          M answers `ask` requests — a FACT, hence deniable
    answered(<M>, ask(x), y)   what M said — a RECORD, hence not yet believed

**A tool may propose; it may never conclude.** What lands is a record that the tool said so, and
an authored rule with an authored grade turns it into a claim — the `arrived` → `says` → trust-rule
path channels have had all along. Checked: delete the trust rule and the answer sits on the record,
believed by nobody, with no act leaving the agent. This is not fastidiousness — let a tool write a
belief directly and §12's weakest link has a link with nothing behind it and `why()` goes dark at the
one place the agent cannot introspect. **The restriction is what makes an unreliable tool safe to be
wrong.** Also checked: the *corpus's* grade governs, so a confident tool cannot launder a weak answer.

**One credit walk reaches rules and tools alike**, and this is the whole of the joint-training
answer. `review`/`blame` follow `applied(...)` licences; a tool's answer carries one; so:

| the tool advised | emitted | jug | credited | blamed |
|---|---|---|---|---|
| `fill(kettle)` | `fill(kettle)` | intact | `did, eff, follow, oracle` | — |
| `smash(jug1)` | `smash(jug1)` | **broken** | `did, eff, follow, oracle` | **`cost, did, follow, oracle`** |
| nothing (declined) | — | intact | — | — |

One line of machinery did it: `Machine._statements()` puts rules and tools in one table, because the
walk follows a licence and *which kind of statement produced this* is a question for the reader.

>**Jointly trained means a shared credit assignment, not a shared update rule.** The trail yields
>*labelled examples* — request, answer, outcome sign — not gradients. The rule side learns by
>rewriting its corpus (`learned()`); a model side would fine-tune on labels the same walk produced.
>Calling it joint gradient descent would be false; calling it one supervisor over two learners is not.

**The twin trap, three more times in one session, and now written down.** Registering `oracle` to
answer `guess` by *name* mints a second `guess` beside the one the corpus writes, so the tool waits
forever for a request nobody can make. An answer built with `g.atom("vessel")` is a node no rule can
name. Both silent, both measured here. **Anything that binds a name must go through the table that
resolves it** — hence `Loader.answerer`, registering a tool in the corpus's scope, because *a tool
answers a request in some corpus's vocabulary*. This matters more for a real model than for a stub: a
model returns **strings**, and every one has to be interned in that scope. Encoded as a control gate.

**New instrument: `python -m ugm.tools`** — 11 gates, 0 failing. Kill-probed three ways (drop tools from
the statement table; stop consulting the binding; make the tool conclude instead of propose), each
failing exactly the checks that should catch it.

**What is still Python, stated exactly.** The answerer's *body* is native and always will be — that
is what a tool is. `_fit`, `_verdict`, `_settle`, `_dispatch` and `_enter` are still bound in Python
rather than through `answers`, so the apparatus does not yet eat its own cooking. Converting them is
mechanical and deliberately not done: a corpus that could retire `_fit` could retire backward reading,
which is §19's carve-out and a different argument.

**What a real model adds that this stub does not test: nondeterminism.** §3 forbids reading a derived
result out of an unseeded source, and a sampled answer is exactly that — two runs diverge with the trail
recording neither the choice nor the reason. A real answerer needs its seed on the record, or it is not
reproducible reasoning. That is the first thing to solve before wiring one.

**Where a model belongs, scored before deciding** — and this table was **wrong about its own top
row**; see the `advisor` section above. It scored *is it safe to be wrong here* and never asked *is
there anything to win*, and at recall the answer is no. Intake (prose → `says`) remains the thing rules
provably cannot do here (raw prose 0/50, book corpus 26%). Writing conclusions directly fails
not-leaking and not-lossy and is still the one placement ruled out.

## Before that: **the learning loop closes**. Commit `learning`.

The user: *shall we tackle learning, so that we start building a working learning mechanism with
whatever we have?* Yes — and "whatever we have" turned out to be enough, because the last commit but
one supplied the missing half without anyone noticing.

**SUPPRESSION IS NOT A DECISION.** Measured before building anything: an episode that smashed a
jug to get water blames the smasher (`['cost', 'did', 'use-jug']`), drops it from what it recommends —
and then **smashes the jug again**. Omitting a rule leaves it exactly where it was, first in authored
order. `learned()` could say *do not recommend this*. It could not say *do that instead*, and only the
second changes a run.

**The missing half was already on the trail, put there by `forgoing2`.** `forgone(A, w)` says *A
was a live way of getting w and something else was taken*, licensed by `applied(<winner>)` — so a
**blamed winner names its own alternatives**. `Machine._instead_of` is that join, and it needs no new
bookkeeping. Third time credit assignment has come out that way.

| | episode 1 | episode 2 | episode 3 |
|---|---|---|---|
| emitted | `smash(jug1)` | **`fill(kettle)`** | `fill(kettle)` |
| the jug | broken | **intact** | intact |
| blamed | `cost, did, use-jug` | — | — |

What it carries forward is one row: `fact prefer(<use-tap>, water, 3)` — *the alternative it passed up*,
not merely the absence of the rule that hurt.

**The control is the finding's proof.** `ugm.learning` re-runs the whole thing with the join
disabled (blame still suppresses, nothing promotes) and the agent smashes the jug **both** times, having
written rows in each. Take the join away and the second episode must go wrong again, or the join was
never what fixed it.

**It generalises, and that is checked rather than inferred.** The row is keyed on the goal's
*relation*, so a run about `pot`/`jug2` — objects the taught episode never saw — takes the tap. The
fresh control on the same world still breaks the jug, so the fixture can fail.

**Why this is possible now and was not two commits ago.** The `experience` session measured an exact
learned table buying **nothing**, and that verdict is stale: it was taken when a losing rule was
*deferred, not rejected*, so the agent took the good route **and** the bad one. `forgoing2` made
arbitration a decision. The arena is now one line of authored order — `<use-jug>` written first breaks
the jug, `<use-tap>` first does not, nothing else differs — which is exactly the kind of choice the
`experience` census found settles two thirds of this agent's arbitrations with no reason at all.

**A guard I wrote returned nothing, silently.** `_instead_of` skipped any `forgone` node with
`has_var` — but a `forgone` node names a **rule**, and a rule node is generic by construction, so it
skipped every real deposit. The guard belongs on the *want* (member 1), which is where `blame` puts the
same guard for the same reason. Found by printing the join's input rather than trusting an empty result.

**New instrument: `python -m ugm.learning`** — 12 gates, 0 failing, including the control and the
transfer pair. Kill-probed: deleting the two-line join fails 3 selftest checks and 4 of its own gates.

**What it does not show, and both are §21 items already.** The promoted alternative is recommended
because something that harmed passed it up, **not because it is good** — in a world where every route
does damage `learned` recommends none, which is right, and offers nothing instead, which is the
non-negative-numerals gap again. And the signal is **one episode deep**: a second `prefer` row for the
same rule and key does not accumulate, because restating is not revising (§8). That is the next thing to
measure, not to assume.

## Before that: **the bundle is authored in the surface**. Commit `bundlefile`.

The user's question, asked before picking up the list below: *shall we move rules to dedicated files
instead of embedding them in Python?* Yes — and it was not tidying. It is §2's expressibility criterion
turned on the apparatus itself, and it **found two silent gaps**.

`Machine._install_bundle` was ~250 lines of `self.rules.rule(IMPLIES, [Member(PLUS, g.rel(...))], ...)`.
It is now four lines that load `ugm/rules/bundle.ugm` through the ordinary `text.py` loader. Same 17
rules, same names, same order, 272 → 278 checks and every instrument unchanged.

**The bundle was data in every sense the design asks for except the one nobody had checked.**
Nameable, reifiable, defeasible — and written in a vocabulary a corpus could not reach. `arrived` and
`not` were absent from `Machine.reserved`, so `<intake>` and `<denial>` were **unwritable by anyone but
the engine**. Worse than unwritable: `Graph.atom` mints a fresh node per call, so a corpus rule naming
`arrived` built a **twin**, matched nothing, and said nothing. That is the trap this codebase has now
paid for five times, arriving from the vocabulary side instead of the minting side.

So `_vocabulary_is_surface_nameable()` runs on every load: a bundled rule reaching for a relation a
corpus cannot name is a **construction error**. Deleting either name now fails `Machine()` — which is
how the two were found, and the probe is in the commit.

**I over-claimed a third gap and the kill-probe caught it.** I said the `?` sign was missing too, so
the two `-invalidated` deviation rules were unwritable. Measured by deleting `"unsure"`: the machine
still builds. `?` was always accepted as a member **sign** (`? ?p`); what was missing was `?` as an
**argument**, which the bundle happens not to use. The asymmetry is still real and still worth closing
— `expects(p, plus)` was writable and `expects(p, unsure)` was not, so a corpus could say *I expected it
to hold* but not *I expected to be unable to say*, which §9 insists is a claim and not the absence of
one. Kept, with its own check, because a vocabulary entry with no user is what `ugm.bundle` exists to
catch.

**Four rows generated by a Python `for` loop is a branch wearing a row's clothes.** The
`deviation-*` family was `for expected, observed, why in (...)`. In the file it is four written rules —
which is literally the design's own test (*adding a connective adds rows, not branches*), and it was
failing it in the one place the design cites as its example.

**Install order is now legible.** §18's tiebreak settles two thirds of this agent's arbitrations
(the `experience` section measured 19 of 30 won by authored order alone). That order was typing order
inside a constructor; it is now the top-to-bottom order of a file you can read as an argument.

**Three checks crashed the runner instead of failing it**, found while probing. Deleting `<intake>`
made `trusting_a_channel` raise `AttributeError: 'NoneType' object has no attribute 'grade'` — so a
mutation that should have sent someone to the argument killed the process three checks in, and every
check after it went unreported. **A runner whose contract is *any False is a failure* has to be able to
say False about an absence.** Guarded; the same probe now reports 27 clean failures.

**My own new check tripped the trap it was written about.** The first version delivered on
`channels.open("user")` and built `g.rel(g.atom("raining"), ...)` — fresh nodes outside the loader's
table — so it failed on twins, in a check about twins. `channels.use` exists for exactly this.

What did **not** move, and stays machinery: the `standing` deposit per bundled rule, the six `on_write`
hooks, and `_forbid`. §21 already calls those honest debt.

`docs/rules-design.md` is still the design and the only doc that argues anything. **This file is a
map, not a source** — where it disagrees with the design doc, the design doc wins.

Everything below the second `# Handoff` line is the **previous** session, kept for its arguments.
Where the two disagree, this header block and the sections directly under it win — in particular its
*state of the code* and *where I would pick up* are superseded by what is here.

## Verify in one go

```
python -m ugm.selftest      373 checks, 0 failing   the runner; any False is a failure
python -m ugm.agreement      28 reads, 12/12        the rule-level read against the native one
python -m ugm.bundle         17 rules, 6 answerers  is every shipped rule and answerer load-bearing?
python -m ugm.backward        7 checks, 0 blind     backward reading, as rules
python -m ugm.compose         5 checks              composition, measured
python -m ugm.modality        (table)               grade vs lifted vs supposed
python -m ugm.workload       25 checks              stopping pays; and what BAD ADVICE costs
python -m ugm.learning       31 checks              does an episode teach the next one?
python -m ugm.tools          11 checks              can a tool be data?
```

**Every instrument prints its COUNT, not only its failures** (commit `counts`). `0 failing` reads the
same whether it ran thirty checks or none, which is how the `magnitude` commit silently deleted ten of
`ugm.learning`'s and nothing noticed.

**`ugm.bundle` now asks §20's question of ANSWERERS too**, in two columns, because *is it
load-bearing* and *may a corpus turn it off* are two questions. And a removal that makes the runner
**raise** prints `raised` rather than a count — a count there is a lie, since the run stopped at the
first check that could not survive the absence.

## The state of the code

**20 modules.** `chain` `graph` `gate` `rules` `channels` `machine` `text` are the engine; `__main__`
is the door; `selftest` `agreement` `bundle` `backward` `compose` `modality` `workload` `learning`
`tools` are instruments; `stratum0` is the rule-level read.

    python -m ugm <corpus.ugm> [--limit N] [--why TERM] [--save FILE]
    python -m ugm --resume FILE

**No phases.** `tick()` is: read `enough` → recall → match (**delta only**) → defeat → forgone →
quiescence → arbitrate → doubt → forgo → apply; plus `_leave`, `_wake`, and two escalations —
`_widen` for a dry shortlist and `_recover` for a domain out of mind.

**Two caches, both semantically load-bearing and each gated by mutations the suite could not see
before they were written**: applications carried across ticks (`_applications`), and the resolved
state carried across ticks (`_state`). *An optimisation of a read is a re-implementation of its
semantics* — `resolve` now has two implementations and only the suite says they agree.

**Seventeen bundled rules** in `ugm/rules/bundle.ugm`, plus **six answerers** bound by
`answers(<M>, ask)` facts (`<fit>` `<settle>` `<verdict>` `<root>` `<remember>` `<re-ask>`), four of
them `standing` so a denial is refused on the record.

**Write-time hooks**: three — `_dispatch`, `_enter`, `_answer`. **Three guards, one move —
*escalate before believing a decline***: `_widen`, `_forbid`, `_notice_open`, and now `_recover`.

**Offline, outside the loop:** `review()` / `blame()` / `learned()` / `refine()` / `induce()`.

**What is still not in the graph**, audited: mirrors of graph facts (`emitted`, `_acted`, `_quieted`,
…), and the genuinely privileged — the one register, the **name tables** (which cannot be in the graph
without making names identity), answerer bodies, and the caches. The hidden-claims bucket is empty.

## Where I would pick up

Nothing on this list is blocking; the engine runs, reports, saves and resumes. In order of how much
they would buy:

1. **The re-ask that closes two stale records.** `achieved` goes stale after a goal is satisfied
   later, and `blocked` goes stale after an escalation brings a domain back — both because a `check`
   was asked once and nothing re-asks. `again` exists for exactly this and nothing ships concluding
   it. One corpus rule; demonstrated inside a real interrupt-and-resume scenario, not hypothetical.
2. **`current_state` is no longer the wall, but the loop still applies ONE application per tick**, so
   tick count grows with the corpus. 10,000 facts is 75s. Batching applications, or keeping the
   `Situation` incremental, is the next structural move if anything needs book scale.
3. **When may a binding be reconsidered** — the last of the original four hats. `binds(plan, ?t, sink)`
   is reference as BINDING, and nothing revisits one. Re-asking did not reach it: a request is a
   proposition and can be re-delivered; a binding is not one.
4. **Experience is one episode deep** (a second `prefer` row does not accumulate), and **rivals are
   noticed only at the tick the choice is made**. Both older, both unmeasured as to whether they matter.
5. **Complementary work cannot be declared** — two rules that should *both* run for one want.

**Standing hazards, none of them enforced.** *An occasion warrants a re-ask only if re-asking cannot
produce one* — now demonstrated to break in two places (`causes`-shaped re-asks, and re-supposing on
`left`). And the `open(?w)` idiom only fires on the `enough` path, not at quiescence.

**The two sibling repos are deliberately dark.** `../pystrider` works against a `main` worktree at
`../ugm-classic` (editable install repointed there); `../harneskills_new` is stale against every ref
and needs real porting. The user's call: leave them, finish the engine.

---

## Since the last handoff: **an agent that can stop**

Pickup item 1, taken because the measurement said it was in front of everything else. One commit,
`stopping`, and it settles two of the item's four questions, corrects a headline number, and opens
one new §21 item.

**`enough(x)` — *there is nothing more worth doing about x*.** A claim, so a rule's to make; the
loop's whole part is to read it before the tick's work and stop. The record is `stopped(<seat>, x)`,
§17's treatment for `arrived`/`emitted`/`left`/`quiet` arriving a fifth time. Nothing ships concluding
it, exactly as the recall budget defaults to off.

| D=8, R=8 | →goal | →end | how | writes |
|---|---|---|---|---|
| exhaustive | 57 | 124 | quiescent | 706 |
| exhaustive + stop | 57 | **59** | stopped | **470** |

**Four things that were forced, not chosen:**

* **read before the tick's work.** Arbitration is total, so a check made after one has run is a check
  made after the move. §16's ordering trap deciding a design for the third time.
* **it routes to `_leave` first.** `enough` inside a hypothesis ends the *branch*, because a frame is
  already the unit of work that can be over. That is *when is a plan settled* and *when is a woken
  rule done* answered at a door that already existed — no new mechanism. What crosses out is
  `likely(enough(g))`, which no relation matches, so a satisfied branch cannot stop its parent.
* **it must not write `quiet`.** `<give-up>` asks its verdict at `quiet`, and `blocked` is an
  aggregate over a **finished** search. A search that stopped because it was satisfied has not
  finished, so writing `quiet` would report every goal it never reached as blocked — the exact
  unsoundness `_widen` exists to prevent, arriving from a second side.
* **it is terminal, where `quiet` is not.** `quiet` continues the loop so a watchdog can key on it;
  *nothing more is worth doing* leaves nothing worth doing. The wind-down case is a new §21 item.

**Recall may not be incomplete about whether to go on.** Once stopping is a rule, *being late to
recall it is being late to stop* — and under a budget the ideal table pushed the rules that read,
notice and stop down the shortlist. Worse: with the apparatus capped out, an *ideal* table reached
quiescence **slower** than exhaustive recall (182 ticks vs 124). So `standing` is now carved out of
the cap alongside `due`. Note what did **not** change: §16 keeps `standing` out of recall's
*ordering*. **Inclusion is a different claim from ordering**, and only the first was taken.

**That corrected the *8 ticks instead of 734* headline, and the correction is the finding.** It
was measured with a budget that also switched the apparatus off — the R-tick run was an agent with its
machinery turned off. Carve the apparatus back in, which stopping requires, and the table's steering
vanishes behind the apparatus's **authored precedence**. That is §13's unresolved blocker (`<ask-fit>`
monopolising arbitration) shown to hide recall's *prize* as well as its cost. **`ugm.workload` cannot
measure recall again until that is fixed** — its gate is now on *stopping* buying something, which it
does, and which can fail.

**`goal` does not distinguish a root goal from a subgoal**, so the general stop rule is not
writable. `{+goal(?w), +?w} ⟹ {+enough(?w)}` reads right and is unsound: `<expand>` writes
`+goal(sub)`, so the agent stops at the first satisfied *subgoal* — measured, tick 51 of a run whose
goal arrived at 57. A root goal is a `goal(?w)` with no `subgoal(?p, ?w)`: a negative existential,
which §12 says a `−` member cannot express. Needs a request, or the licence readable in the graph —
both already §21 items (§6's *a root goal is never checked* is the same gap from the other side).

**Two checks the habit caught.**

* `ugm.selftest`'s widening negative control **could no longer fail**, and the reason mattered more
  than the check: §14's `by_conclusion` index had already moved backward reading off the shortlist,
  and the carve-out removed the other path. So the *verdict* half of the widening argument is now
  guarded twice over — reported as such, with a fixture that still can kill the line substituted for
  the one that cannot.
* My own new check for `enough`-inside-a-hypothesis was **blind** — it asserted `holds("resumed")`,
  an atom that never appears, so it passed under every mutation. Found by deleting `_enough` and
  counting. Replaced by a contrast pair; and that turned up **stopping is only as prompt as the
  recall and arbitration of the rule that says stop**: an unmarked stop rule takes one more step
  first, because it is one competitor among many.

## ...and the follow-up: **no goal is dropped silently**

The user's read of the above: *there should be an outer loop, always on, that checks whether any goal
is still open* — and, asked what to do when it finds one, *ask the user; ideally the goal is open
because no solution was found.* Commit `openloop`.

**The first version of `enough` walked away from a goal in silence.** Measured: two goals, a stop
rule on the first, and the run ended with the second neither achieved nor blocked nor pursued, and
nothing recording it had been open. The stop was on the record; the abandonment was not. §2's
not-lossy criterion failing at the place §19 had just claimed to close.

**It is a veto, not an outer loop and not a rule.** An always-on check at a fixed point in the loop is
structurally a phase, and *if I still have a question, there is more worth doing* as a corpus rule is
a convention every author must remember — the kind this design keeps finding it has lost. So: §19's
carve-out a fourth time, `open(<w>)` deposited before the stop is made. **That makes three guards that
are one move — escalate before believing a decline**: `_widen` at a dry shortlist, `_forbid` at a
write, this at a stop. None is a phase; each answers one question at one machinery decision.

**An outstanding goal OUTRANKS an `enough`; it does not delay one.** The first attempt had the
veto cost a tick and let the stop stand — and the diagnosis never appeared, because reacting to an
open goal is ordinary reasoning of whatever length it takes. So once vetoed at a seat, `enough` is not
consulted there again; the agent finishes at quiescence. **Costs nothing where the saving was
measured** (achieved or genuinely unreachable goals yield no new work — workload still 59 ticks vs
124), and costs the whole saving exactly where saying *enough* was a mistake.

**A bundled rule I added was dead, and `ugm.bundle` said so before a check existed.**
`+open(?w) ⟹ +verdict(?w)` looked exactly parallel to `<give-up>` and was deleted: because an open
goal outranks the stop, a run with one always finishes at quiescence, so `quiet` is written and
`<give-up>` already asks the verdict. The *occasion* is load-bearing (it records which goal was nearly
dropped); a second way to ask about it was not.

**The reaction is a corpus rule, and the round trip needs nothing new.** One line —
`{+open(?w), +blocked(?w)} ⟹ {+doing(ask(?w))}` — **and it has a precondition nobody wrote
down: `open` exists only on the `enough` path.** The veto deposits it when the agent tries to STOP; an
agent that merely runs out of work never gets one, so this line does not fire without a stop rule in
the corpus. `blocked` is the quiescence-side record and `open` the satisfaction-side one, and they do
not co-occur — key on `{+goal(?w), +blocked(?w)}` for the quiescent case. Found by writing the
documented line into a fixture and watching it ask nothing. — and `doing` crosses at the write, the run ends
because a question is not work, and a later utterance resumes it through `<intake>`. Checked end to
end. Note what it asked about: not the goal it was given, but `heat(kettle)`, the precise subgoal
backward reading found it was missing. Nothing arranged that.

>**The loop may end. It may not end quietly on something it was asked for.**

Left open, and recorded in §21: the veto fires **once per goal per seat**, which is what makes it
terminate — so the guarantee is *the agent was given the occasion to react*, not *the goal was
disposed of*. An agent that reacts by doing nothing stops on the next attempt with the goal still
open, recorded but still dropped. The stronger property wants a notion of a goal being **discharged**,
which is the same missing notion as *when is a request re-askable*.

## ...and the third: **experience, and the arena it has nothing to decide in**

The user's read: *we are now observing situations where deciding the best thing to do is not
straightforward — these are the cases where experience and heuristics should guide.* Commit
`experience`. Right, and measuring where those situations actually are produced the session's most
uncomfortable number.

**Credit assignment needs NO new bookkeeping.** R5 already licenses every derived entry with
`applied(<R>)` because the trail is load-bearing for §12's weakest link — so walking back from what
was achieved reaches the rules that produced it, and only those. Built as `review()` / `helped(<R>,
<key>)` / `learned()`. Measured with a rule that ran and contributed nothing (`<idle>`) and a rule
that would have served and never ran (`<fill>`): both correctly earn nothing.

* **Offline**, and that is the user's own standing position — credit needs the outcome. It is also
  forced: a satisfied run ends at `stopped`, which is terminal, and those are the episodes most worth
  learning from. So it is a pass over a finished episode, and the loop does not change.
* **The key is the goal's RELATION, not the goal** — a row keyed on `boiling(kettle)` is true of one
  episode, and a table that cannot generalise is a cache. (`_in_play` already keyed on goals; it keyed
  on the *term*.)
* **What it takes forward is corpus TEXT** — readable, editable, deniable. §19 puts experience in
  recall because being wrong there is recoverable, and a weight is not recoverable.
* **Failure credits nothing and blames nothing** — a failed episode may have been an impossible one.

**And an exact learned table bought NOTHING, which is the real finding.** Same ticks as no table
and as the hand-authored ceiling. Where the choices actually are, over one episode:

| arbitrations | 30 |
|---|---|
| won by the **apparatus** | **26** |
| won by a domain rule | 4 — and preference already decided all four |
| won by **authored order**, no reason at all | **19** |

>**Experience has almost nothing to decide, because the apparatus wins most of the agent's choices —
>and the apparatus is deliberately unrankable.** `standing` flattens every bundled rule to one rank,
>so their mutual precedence is *install order*.

So §13's claim *the apparatus's order is authored on purpose* is true of the pairs anyone thought
about and **incidental for most of them**. Two thirds of every choice is settled by typing order, and
neither mechanism built to notice that can see it: `close` excludes `standing` ties by design, and
`review` credits rules on the support of a *conclusion*, which the apparatus's bookkeeping never joins.

**Two of my own checks were blind and the kill-probe caught both** — `<fill>` never applied, so any
scheme excluded it and the "credits what was used" check tested nothing; and the generalisation check
asserted a run that would have succeeded anyway. Fixed with `<idle>` (applies, concludes, earns
nothing) and by checking the *row format* directly.

## ...and then the floor gave way: **ARBITRATION IS SCHEDULING, NOT DECISION**

**The recommendation in the paragraph this replaces was wrong, and measuring it is how.** I proposed
ordering *within* the standing tier, fed by a credit signal reaching bookkeeping. Both halves were
prototyped. **Neither pays** — tier ordering changed the sequence of applications and left ticks,
writes and time-to-goal identical, because the apparatus is a dependency chain and permuting a chain
cannot shorten it. *Narrowing changes the order, not the amount* is as true of arbitration as of
recall; ordering pays only where work is **avoidable**.

Then the user's challenge: *is that because the fixtures are too few/too simple, and random actions do
not compromise the situation, where in real life they often do?* Right to ask, and the answer is worse
than fixture size. Built a world where a wrong choice loses a goal — two ways to get water, one breaks
a jug another goal needs:

    emitted: ['fill(kettle)', 'smash(jug1)']

>**The agent did BOTH.** A rule that loses arbitration is **deferred, not rejected**, and a loop that
>runs to quiescence applies every one eventually. **A choice that cannot be forgone is not a choice.**

These are *acts* — dispatched at the write, gone. Three consequences, one fact from three sides:

* **Nothing for experience to be experienced about.** *Choose the better rule* has had no
  measurable content because the agent takes the better rule **and** the worse one. This is upstream of
  recall, preference, doubt and learning — all four assumed arbitration decides something.
* **It is a safety property first.** The only thing that can stop an act is §19's norm veto, which
  needs to know in advance which acts are bad — exactly what experience was meant to supply.
* **Credit reinforces the mistake.** `review` credited the **smashing**, not the filling, because
  smashing was on the support of the water achieved. Outcome credit over an agent that cannot forgo
  learns to prefer whatever was on the winning path, including what it should have declined.

Two more, both existing §21 items now *demonstrated*: nothing retracts a conclusion whose support was
withdrawn (the agent ends believing it has juice **and** that the jug is broken), and whether the
damage mattered was settled by which rule was typed first.

Recorded in `ugm.selftest` as `arbitration_is_scheduling_not_decision` — four checks that pass on
**today's wrong behaviour**, so the day it changes they fail and send someone to the argument.

## ...and two user proposals, both measured, both right

**1. *Once you apply a rule you mint new nodes, the focus should shift, and that should make the
not-chosen rule not useful any more.*** Tested at its simplest — the winner **consumes** the goal
instead of sitting beside it (`-goal(water(?w)), +pursuing(water(?w), fill(?w))`). It works, with **no
engine change** and no new primitive: only `fill(kettle)` is emitted, the jug survives, both goals are
achieved. Forgoing falls out of the shift, because what the alternative was matching is gone.

Two interactions found and **not yet resolved**, so this is not built into the bundle:
* it **breaks credit** — the achieved goal is no longer a goal, so `review` cannot find it (credit
  dropped to `['squeeze']`);
* it **commits before knowing** — retiring a goal on *intending* means a failed act loses the goal
  silently, and the `openloop` veto keys on `goal(?w)` so a retired goal cannot veto.
The `pursuing(w, act)` node is the trace both repairs would follow. The underlying question it raises:
**a goal is a commitment, not a belief.** Beliefs accumulate; commitments are taken up and discharged.
Treating them alike is why the agent pursues a goal forever and several ways at once.

**2. *Maybe splitting a task in subgoals could help learning.*** Right, and specifically for the half
that was broken. Commit `subgoals`.

**Splitting is what makes BLAME sayable.** `review` refuses to blame because a failed episode may
have been impossible — many rules, one outcome, no author. A lost **subgoal** has one, and the
difference is §9's:

| no entry at all | it was never reached. Many causes, no author. |
|---|---|
| an entry says `−` | something **made** it false, and that entry carries a **licence**. |

So `blame()` is the credit walk run over a denial. Measured: from a lost `intact(jug1)` it reaches
`['cost', 'did', 'use-jug']` — **the decision, not just the physics**.

**The decomposition named the damage without anyone anticipating it.** Backward reading had already
expanded `juice(jug1)` into subgoals including `intact(jug1)` — so the thing the *other* branch broke
was already a goal. Nobody wrote it down; §19's own machinery produced it. That is what splitting buys.

**It repairs the demonstrated bug.** `learned()` now suppresses rules that harmed, so the jug-smasher
is credited by the raw walk and **not** recommended. Suppression rather than a negative score: the
table's numerals are non-negative, so *how badly* is not sayable yet, only *at all*.

**Blame needs a denial, not an absence.** Most unachieved subgoals in a real run are **generic**
(`heat(?a, kettle)`), produced by expansion and never meant to hold as stated. Counting them as
failures blames every rule for every search — the *shortlist that ran dry* error again, mistaking
*not reached* for *shown false*. Killed three ways in the probe, including "blame everything applied".

## FORGOING — built. Commit `forgoing2`.

    forgone(<R>, <w>)      R was a live way of getting w, and I took another one

A **fourth** way for a rule not to run, and the first that is a **decision**: defeat says a rival is
better, the veto says never, recall says it did not come to mind. This says *it was reasonable and I
chose otherwise.*

**Alternatives are read off the EVIDENCE, not off `fits`.** An application that consumed `goal(w)`
is a response to wanting `w` — the same comparison `supersedes` makes, over a trail already kept.
`fits` asks whether a consequent could *be* the goal, which is backward reading's question and the
wrong one: `<use-tap>` concludes `doing(fill(kettle))`, fits nothing, and is plainly a way to get water.

**A deposit ABOUT THE ALTERNATIVE, not a retraction of the goal.** The user's version (consume the
want) works with no engine change, and was rejected on the two measured interactions: credit cannot
find what it achieved, and a failed act loses the want with nothing left to notice (the veto keys on
`goal(?w)`). Depositing keeps the goal, keeps credit, keeps the guarantee.

**Passing up is the DEFAULT; complementary work is the exception.** The one judgement, made on
which error is **recoverable**: forgo-by-default under-does and the goal stays open (veto → `open(w)`
→ hand it back); defer-by-default smashes the jug, and that cannot be taken back.

**Retry is a corpus rule, not machinery** — §21's backtracking arriving as a *consequence*:

    rule <retry> = implies( { +open(?w), +forgone(?r, ?w) }, { -forgone(?r, ?w) } )

Needs three things to meet that were each built for something else: `enough` makes the agent try to
stop, the veto refuses and deposits `open`, this reads it. Checked end to end — the alternative is
taken up and the goal reached.

**The apparatus is exempt on both sides** (§13's carve-out, fifth time). Nearly every bundled rule
consumes `goal(?w)`, so without it, applying any rule forgoes backward reading entire. Measured by
removing it: 5 checks fail.

**Result:** one act emitted not two, the alternative's cost not paid, credit names `use-tap` (the
choice made) rather than `use-jug` (the one passed up), and *what did you not do, and why* is on the
trail.

**Six checks failed when this landed — all six were the GAP checks written to record the old
behaviour.** That is them working: they were labelled *passes on today's wrong behaviour, so the day
it changes they fail and send someone here*. Rewritten as guarantees
(`taking_one_way_passes_up_the_others`). And `subgoals_make_blame_sayable` needed a **new fixture** —
with forgoing, a world with a safe alternative no longer produces harm, so it would have measured the
forgoing rather than the blame. It now has no tap: sometimes the only way costs something, and that is
the case blame is for.

Left open, and carried into the pickup list at the top of this file: rivals are noticed **at the tick
the choice is made**; *complementary* work is now a case a corpus must declare; and **how badly** a
rule cost something is unsayable, because the table's numerals are non-negative. The
open question is not how to implement it but what it *is* — a rule can be defeated (`overrides`,
`supersedes`), forbidden (the veto), or never proposed (recall), and none of those says *this was a
live alternative and I am taking the other one*. Constraints the shape must satisfy: not a filter in
the loop (§18); the decision on the trail (§2's not-lossy, and credit needs it); and it must survive
being wrong, since the point is that the alternative was reasonable.

**After that:** the old item 1's other two questions, which are a different shape from
the two now answered — *when may a request be re-asked* and *when may a binding be reconsidered*.
`enough` needed the loop to do **less** and one fact sufficed; these need it to do something **again**.
Then old item 2 (acting on doubt), which was blocked on stopping and may now be unblocked.

Everything below this line is the previous handoff, still accurate except where the above corrects it.

---

# Handoff — 2026-08-11

Branch `restart`. `main` still holds the old 46-module engine on purpose.

`docs/rules-design.md` is still the design and still the only doc that argues anything. **This file
is a map, not a source** — where it disagrees with the design doc, the design doc wins.

---

## Verify in one go

```
python -m ugm.selftest     278 checks, 0 failing        the runner; any False is a failure
python -m ugm.agreement     28 reads, 12/12 exercised   the rule-level read against the native one
python -m ugm.bundle        17/17 bundled rules exercised  is every shipped rule load-bearing?
python -m ugm.backward       0 failing, 0 blind         backward reading, as the rules that replaced the phase
python -m ugm.compose        0 failing, n steps -> 1    composition, measured
python -m ugm.modality       (table)                    grade vs lifted vs supposed
python -m ugm.workload       0 failing                  can this workload measure recall at all?
```

`ugm.bundle` re-runs the whole suite once per bundled rule; it takes ~20s (it took five minutes
before `theread`).

---

## What happened, in order

The session began by reviewing `rules-design.md` and ended with four of five interpreter phases
gone. Ten commits:

| commit | what |
|---|---|
| `spine` | the doc rewritten around a **floor / bundle** split (1902 → ~2400 lines, now 2999) |
| `stratum0` | the read written as rules; `ugm.agreement` |
| `intake` | `says` becomes a bundled rule |
| `acting` | dispatch moves to the write; `did` and `assert-act` become rules |
| `surprise` | deviation becomes four rules; `ugm.bundle` |
| `supposing` | supposition stops owning the loop |
| `own seat` | reports stop landing inside hypotheses |
| `mention` | mention propagates through bindings; rules can reason about rules |
| `fit` | match as a request; `ugm.backward` |
| `delivery` | the boundary calls in; the tick loses its first line |
| `check` | the second request; backward reading entire, in five rules |
| `handoff` | this file |
| `denial` | §9 settled by measurement: sign **and** `not`, translating one way |
| `compose` | pattern-against-pattern is **unification, not match**; composition built and measured |
| `occasions` | leaving a hypothesis and running out of work become **facts**; callbacks and watchdogs |
| `nophases` | the last phase deleted. `tick()` has no line a rule could have written |
| `recall` | §19's first slice: `prefer(<R>, k)` as facts, a budget, and widening |
| `norms` | §19's carve-out: a prohibition is a **veto at the gate**, never a competitor in recall |
| `naming` | a **fact may carry a name**; a named norm is a node rules can retire |
| `reference` | reference is **binding**; the walk is one order; the naming claim corrected |
| `theread` | the read indexed — **67× on the goal fixture**; and `causes` was orphaning the register |
| `workload` | a workload recall can be measured on — and **recall cannot pay until the agent can stop** |
| `better` | preference **orders** rather than excludes; relevance is derived, not authored |
| `lookup` | *what could produce this?* becomes an **index, not a scan** — 13× fewer ticks to the goal |
| `doubt` | preference is a **score on the grade scale**; doubt is a tie, and a tie needs no threshold |
| `knob` | *close* is a knob, so it is a **fact**: `tolerance(2)`, over a table that carries a **score** |

### 1. The spine changed

The user's challenge: **prove `moment`, `entry` and `sign` cannot be open class.** They cannot. They
are the agent's *internal representation of reality* — teachable, replaceable, and the thing an agent
reasons better by having. So the doc is now four parts: **the floor · the internal representation of
reality · what it allows · gates**, and nearly everything is convention.

The floor is five items on **three grounds**, which matters because flattening them makes all of it
look inevitable:

* **irreducible** — variables+substitution, one total step, the register
* **by guarantee** — the stamp (reducible, but reducible provenance is forgeable)
* **by economy** — ordering (fully reducible; its reduction turns linear matching into subgraph
  isomorphism)

`recall` was never a primitive. Descent to the floor is **grammaticalization** and must be *measured*,
not decided in a sitting.

### 2. The bootstrap is solved

Only one of four steps of applying a rule is circular. **Stratum 0** = rules whose antecedent members
are all structural; they are applied without a read, and the criterion is decided by scanning an
antecedent. Three regresses (reading, selecting, proposing) all escape into **a function, not a
search**.

Consequence worth keeping: stratum-0 rules are ordinary data, so **the read is replaceable at run
time**.

### 3. Four phases left the loop, and each one taught something different

| | |
|---|---|
| **intake** | a phase can hide a **precedence claim** — "runs before any rule" became an authored order a corpus can override |
| **acting** | it was in the wrong place *and the doc already said so* (§16 puts dispatch at the write). `<assert-act>` made §18 concrete: delete it and the agent still acts, still knows it acted, but no longer assumes success |
| **surprise** | a branch hides **how many claims it was making** — one comparison became four rules, three of which nothing could kill |
| **supposing** | the hard part was not the register (3 lines) but a **nested `run()`**. Entering is a write, leaving is quiescence |
| **delivery** | **being machinery never made it a phase.** An arrival is an external event; the boundary calls in |

>**A convention hidden in vocabulary is easy to see and cheap to move; a convention hidden in
>control flow is invisible and expensive.** The census counts names, and names were the easy half.

### 4. §5's wall came down in two halves

**Quiescence is a third place the machinery declines, and it declines silently** — §2 named only
match and write. A rule reasoning about rules was dropped as *nothing left to do*.

**Use/mention by authorship was too strong**; the replacement is *mention propagates through
bindings*, checkable because consumed entries are already recorded for the trail.

**`match` from a rule is a request, not a sixth primitive — and it cannot answer with a binding**,
because a rule cannot apply one. *Match and substitute travel together.*

### 5. Two occasions, one mechanism — and the wall was protecting something

Two questions turned out to be one. *What runs on the way back out of a hypothesis?* and *what stops
reasoning dying quietly with a goal still open?* Both want something to happen at a moment the
machinery owns and no rule can name — so both get §17's treatment for arrivals and emissions:
deposit the smallest unarguable record, let rules say what it means.

    left(<frame>, <assumption>)      written by `_leave`, after discharge
    quiet(<m>)                       written by `_wake`, once per seat

**`quiet` closes §5's third silence.** Match and write were the two named places the machinery
declines; quiescence was a third that said nothing at all. It is also the moment an *aggregate over a
finished search* becomes legitimate — which is where §21's homeless `blocked` belongs. A watchdog
needs nothing more: it is an ordinary rule with `+quiet(?m)` in its antecedent, inert until the loop
stops because nothing else writes that. **The trigger is the fact** — no trigger table, no registry.

**A callback is a pointer to a rule, and it may not be a call.** `+resume(h, <R>)` hangs a rule on a
hypothesis; `<resuming>` picks it up and can only say *this rule's turn has come* (`+due(<R>)`),
because §5 forbids a rule applying a rule. A `dormant` rule is not proposed by ordinary recall; a
`due` one is. So a callback is **directed recall, not invocation** — and that is stronger than a call:
the woken rule still has to match, can still be defeated, still competes, still yields to a surprise.
Adding continuations did not weaken *nothing owns the loop*.

It also lands on §19's reserved seam: `dormant`/`due` are the first thing a corpus has ever been able
to say to `_recall`.

Three things this cost, and two of them were bugs that had been invisible:

* **substitution was minting twins.** Rebuilding a consequent goes through the interning constructor,
  so descending into a rule node returned an interned *copy* — the pointer named a rule that did not
  exist and every question about the real one answered nothing. Fixed in `substitute`/`ground`: a
  subterm nothing changed is returned unchanged.
* **mention had no source.** §14's *mention propagates through bindings* needs somewhere to start; a
  rule authored naming a rule (`<...>` in its consequent) is it. Without it a rule attaching a rule
  was dropped by quiescence as *nothing to do*.
* **the occasion persists.** `quiet` is an entry, not an event, so a watchdog is armed from quiescence
  onward, not fired once. One whose conclusion re-arms it runs to its budget. Likewise `due` is not
  consumed — a woken rule stays awake, which is fine only while recall is exhaustive.

### 6. The last phase went, and the count is zero

`_expand_goal` is deleted. `tick()` is now recall → match → defeat → quiescence → arbitrate → apply,
plus the two things a register owes: `_leave` when a hypothesis runs out of work, `_wake` when the
loop does. **There is no line in it a rule could have written.**

Backward reading ships as five bundled rules over three requests — `<ask-fit>`, `<plan>`, `<expand>`,
`<ask-check>`, `<give-up>`. What made the last one possible is the `verdict` request: `blocked` claims
that **no** rule fits, an aggregate over a finished search, and `quiet` is the fact that says a search
has finished. The machinery answers it by counting `fits` and `achieved` entries **the rules
produced** — it runs no search, so *which rules were considered* stays recall's business.

Two supporting changes:

* **rules are data when authored** (`RuleSet.on_rule` → `Machine.reify`). Backward reading enumerates
  `+rule(?r)`, so a rule loaded after someone called `reify_all()` was invisible to it with nothing
  reporting so. `reify_all()` is kept and idempotent.
* **R2 moved from the licence to the trail.** The phase stamped subgoals `wanted`; now `<expand>`
  writes them, so the licence is `applied(<expand>)` and the reading is recovered one hop back —
  `<expand>` consumed a `need` entry, and `_fit` licences everything it answers `wanted(<R>, goal)`.
  Checked by walking the trail rather than by trusting a stamp.

**What it cost, measured.** 98 steps where the phase took ~10 on the same corpus; `ugm.backward`'s
fixture is 194 steps / 411 writes. `ask-fit` asks every reified rule about every goal, which is
exactly what §19 exists to narrow — the phase hid that cost by hard-coding the narrowing.

**Two gaps this made visible, neither of them new:**

* **a root goal is never checked** for satisfaction. `<ask-check>` keys on `subgoal(plan, ?w)`, and
  *a goal with no plan* is not expressible. Checking every goal binding-free would reintroduce §18's
  sibling failure, so this needs a real answer, not a rule.
* **a request can only be made once.** `<ask-check>` asks when the subgoal appears; if forward
  reasoning satisfies it three ticks later, nothing asks again, because re-concluding `+check(p, w)`
  changes nothing and quiescence drops it. This is why `ugm.backward`'s historical 29th fact
  (`achieved(water(kettle))`) is no longer produced — recorded there as a claim about the phase, not
  as a current output. A re-ask needs a fresh request node; §21.

### 7. Recall stops proposing everything

§19's seam is open. `prefer(<R>, k)` is a table of **ordinary facts** — *when `k` is in play, bring
`R` to mind* — authored for now, learnable later from the trail R5 already deposits. `recall_budget`
is `None` by default, so behaviour is unchanged until a corpus claims something.

**The key is not the register.** Attention *is* the register (`Machine.focus`, a `Frame(seat, topic)`
— §4's one privileged pointer), and that is why it cannot be the key: a seat is a fresh moment every
tick, so a table keyed on it never sees the same key twice. The key is **a relation in play**
(`_in_play` = the relations in the current moment's delta — *what just changed*). That is one method
wide, deliberately; a better key replaces it without touching the loop, the table, or any rule.

**A shortlist that ran dry is not a search that finished** — and this is a *soundness* condition, not
a quality one. `<give-up>` asks its verdict at `quiet`, and `blocked` is an aggregate over a finished
search. So quiescence under a budget escalates to the exhaustive pass first (`_widen`, step state
`widened`), and only its silence writes `quiet`. Take the line away and the same corpus gives up on a
goal it can reach — checked, and the check is shown able to fail.

**Randomness was considered and not taken.** §3 forbids reading a derived result out of a set, and an
unseeded top-K draw is that bug wearing a hat: two runs diverge and the trail records neither the
choice nor the reason. The tie-break is authored order, the same one arbitration uses. If exploration
is what randomness was for, §19 already has the better answer — the exhaustive pass on novelty or a
schedule, which injects what a draw *from the shortlist* structurally cannot.

### 8. Norms come off the recall path

§19's carve-out, and it is the one place the design refuses to be incomplete:

>Recall may be incomplete about what to do. It may not be incomplete about what you must not do.

`forbidden(<pattern>)` is a norm. Its argument is a **description** — `forbidden(doing(harm(?x)))`
names a class of acts the way `ant(<R>, heat(?a, ?w))` names a class of premises. It is never
proposed, matched or arbitrated: `Gate.veto` consults it on every write, **before the deposit**, so a
forbidden entry never exists — not even briefly, and not for an `on_write` hook to see. Dispatch *is*
an `on_write` hook, so that is what keeps the act inside the agent instead of emitting it and
regretting it.

Cheap because it is indexed by what is about to be written (§3's instances-by-relation): only norms
whose pattern shares the proposition's relation are resolved.

**A refusal writes.** `refused(p, sign, <norm>)`, licensed by the norm. A veto that deposited nothing
would be a fourth silent decline, and silence about norms is the exact failure being designed against.

Three things fell out rather than being arranged: quiescence still terminates (the *refusal* is what
stops the rule re-applying — otherwise a norm is a livelock); a norm forbids `+` only, because
bringing about is asserting; and a norm is still an ordinary belief, resolved at the writer's own
position.

### 9. Naming a statement, and what it separated

Stating a norm was not enough. A norm's argument is a **description**, a description is an authored
statement, and §8 scopes a statement's variables to it — so `forbidden(doing(harm(?x)))` written twice
is *two nodes that say a similar thing*, and denying the second leaves the first forbidding, silently.
**Restating is not revising.** That is §8's own rule about rules arriving somewhere it had not been
noticed.

The repair was already in the surface. A fact may carry a name:

    fact <no-harm> = forbidden(doing(harm(?x)))
    fact -<no-harm>

`<...>` is the namespace of **statements**, and a rule is a statement — so it is one table, not two.
A rule and a norm sharing a name would be two things with one name, which is what the marker exists
to prevent.

A separate consequence, about the carve-out rather than about naming:

>**§19 keeps norms out of recall. It never said they were beyond argument.**

A rule can retire a norm on evidence — `{+says(fire, evacuate, +)} ⟹ {-<no-harm>}` — trail intact,
with the refusals it made beforehand still on the record. **Unconditionally consulted** and **entirely
contestable** are different properties.

**Naming is not what separated them.** Measured afterwards: a rule could always do this *without*
the name, by describing the norm's shape — matching a generic antecedent against a stored description
treats the description's variables as ordinary nodes, so `?y` binds to the stored `?x` and
substitution rebuilds exactly the node written. Naming buys **authoring** (a second surface statement
about one description) and a handle for facts that are not about its shape. It never bought
reference.

Forced, not chosen: a rule may conclude about a named fact and a named fact may be about a rule, so
the loader does three passes — name what is self-contained, then rules, then everything else. A name
needs only its node, and a statement referring to no other statement can be built without one.

### 10. Reference is binding, and the walk was two orders

The question was *what else wants a name — a supposition, a plan?* Answer, measured: **mostly nothing
does.** A plan, a hypothesis, a rule and a norm are all referable already, because anything deposited
as an entry can be bound by an antecedent, and **binding is reference**. Language works the same way —
it says *the plan we made before*, not a name. Names are for the exceptions.

What binding does not supply is **which one**, and that turned up a live bug. Several entries match
one description; the walk decides which is tried first, and the walk disagreed with itself:

* `Moment.ancestors()` — newest moment first
* a moment's `delta` — oldest entry first

So two candidates deposited by `implies` (same moment) came out in the *opposite* order to two
deposited by `causes` (different moments) — and which connective a rule used has nothing to do with
reference. One `reversed()` in `current_state` makes it one order throughout, and *a description
resolves to the most recent* is now a claim with a check behind it instead of an accident.

**It changed a result, and the change is the finding.** `ugm.backward`'s sibling-agreement fixture
flipped: with the taps authored one way the plan now succeeds, the other way it still blocks. Same
world. Because:

>**Reference resolves to the most recent, and nothing reconsiders.** `_settle` takes the first entry
>that satisfies a subgoal and never returns to it. Checking siblings inside the plan's bindings stops
>a wrong plan being reported as a good one; it does not *find* the right one.

`ugm.backward` now runs both orders and prints both outcomes — §21's backtracking item measured rather
than asserted. And the old fixture was, it turns out, measuring the walk order rather than the
guarantee.

**One bug fixed on the way**: `discharge` dropped `mention` when carrying a conclusion out of a frame,
so a conclusion *about a rule* drawn under a hypothesis was refused by the gate — §14's propagation
with a hole in it at the one place conclusions change hands.

### 11. Where the cost actually was — and it was not recall

The question was *what is load-bearing for a working system — recall, learning?* Measured first, and
the answer was neither.

The goal fixture is an n-rule forward chain with one goal at the end:

| rules | before | after |
|---|---|---|
| 2 | 1.56s | 0.07s |
| 4 | 7.00s | 0.19s |
| 8 | 54.9s | 0.82s |
| 16 | ~7 min | 4.68s |
| 32 | — | 37.1s |

**67× at n=8.** `ugm.selftest` went 19s → 1.8s; `ugm.bundle` five minutes → 19s. Nothing about the
semantics changed, and 208 checks agree.

**The first attempt was wrong and is worth recording.** The obvious read of the cost was *recall is
exhaustive*, so recall became a request (`+recall(g)` → `+recalled(<R>, g)`) to make narrowing reach
inside an antecedent. It made the default **twice as slow** and broke a soundness check. Profiling
afterwards:

* `chain.resolve` — **86% of runtime**, 415k calls
* `current_state` — called **2043 times for 123 steps**: once per rule per tick, rebuilding and
  re-resolving the entire state each time

So three changes, each measured before the next:

1. **the walk, once per tick** instead of once per rule (`match` takes the state) — 8.6×
2. **the state, indexed by (sign, relation)** — an antecedent member with a fixed relation no longer
   unifies against every entry. §3 gives the substrate exactly this index and the argument was just as
   true of the state, where nobody had made it. A bare-variable member still scans everything, which
   is correct — `+?p` genuinely is about anything.
3. **the read, indexed by proposition** — `resolve` scanned every entry ever deposited to answer a
   question about one. Now it scans that proposition's entries, which are almost always one. The two
   orderings (latest locus, then latest deposit) become a single comparison on
   `(locus.depth, seat.depth, position)`, and containment still costs a real ancestry test because a
   depth comparison cannot survive a fork.

**`_recall` narrowing cannot reach an antecedent, and that stands.** `<ask-fit>` matched **72 ways**
in one tick with four domain rules. Recall narrows which rules are *proposed*; a cross product in an
antecedent is unaffected. The recall-as-a-request branch is stashed, not deleted — but it is not
needed for cost any more, and it should only come back with a measurement behind it.

**A bug the fixture found while trying to measure something else.** Applying a `causes` rule minted
a **fresh frame**, dropping the parent, purpose and wrap. Under a hypothesis that orphaned the
register: `_leave` could never fire, the frame was never discharged, and everything concluded under
that hypothesis stayed inside it with nothing saying so. §4 allows one register; advancing it is a
*seat move* (`Gate.reseat`), not a new frame. Discharge then needs the frame's **origin** rather than
its current seat — those stop being the same thing the moment it moves, and reading it off `seat`
carried out only the last moment.

The index is gated against a brute-force walk over a world that forks and revises — 2448 comparisons,
because replacing a walk with an index is exactly the change that is right for a fixture and wrong for
a fork.

### 12. A workload recall can be measured on — and what it measured instead

The question was *how do we build a big enough workload; should we take `../pystrider`?*

**Not from pystrider's rules.** `pystrider/rules/*.mf` are microfunctions — `ATTR`, `CONST`, `JMPNOT`,
`DISPATCH` — the ISA-with-opcodes floor this design rejects, and CLAUDE.md is explicit that nothing is
ported without re-deriving it. It is 532 lines, so it is not "big" either. What *is* worth taking is
the shape of `experiments/vocabularies/` — business, ux, bridge: **separate worlds that must be
joined**. (Two memories warn against pystrider; both are about *gating* on it as a consumer of the old
engine, which this is not.)

**Size was never the problem.** On a 30-rule chain, between one and eight rules match per tick — and
since `theread` indexed the state, a rule that does not match costs almost nothing. A perfect table
could not beat exhaustive recall there at any n.

>**A shortlist pays only where many rules MATCH and are useless.** Scale is not the requirement;
>**selectivity** is.

So `ugm.workload` builds D domains × depth R, all seeded, one goal in one domain — every domain's
rules match from the first tick, and D−1 of them are irrelevant. And its first result was that an
ideal, hand-authored table bought **nothing**:

```
  D  R   recall                   ->goal  ->quiet  w@goal  writes
  8  8   exhaustive                  734      801    1798    1873
  8  8   budget 8, no table         1468     1601    1798    1873
  8  8   budget 8, ideal table         8     1593     346    1881
```

The table is **perfect** — it reaches the goal in exactly R ticks, 92× fewer, with 5× fewer writes.
It was invisible because the `->quiet` column is the same for all three:

>**Recall cannot save work in a machine that runs to quiescence.** Narrowing changes the ORDER in
>which everything is done, not how much is done. The prize is real, and only an agent that can
>**stop** collects it.

So the thing in front of learning is not a bigger corpus. It is a reason to stop — and that is the
same question as *when is a plan settled*, *when is a `due` rule done*, *when may a request be
re-asked*, and §21's backtracking. Four hats, one head.

Two things `ugm.workload` is not. The table is a **ceiling, not an algorithm** — authored, naming
the answer, learning nothing. And its gate is that the table must buy something: if it ever stops
doing so, the workload has become the n-rule chain again with more rules in it.

**`_in_play` is the wrong key for goal-directed work.** It keys on what just changed, and in this
workload every domain is always in play. The key that would work here is what the agent is *trying to
do*. The hand-authored table sidesteps it by naming each rule's own antecedent relation.

### 13. Choosing the better move — where it belongs, and what it isn't

The framing that started it: *recall should lead the agent to choose better rules instead of doing
dumb things — given many applicable rules, choose the best.* Cost was the wrong lens; a bad choice on
an irreversible step is a mistake, not a slowdown.

**Relevance was already computed and thrown away.** `_fit` writes `fits(<R>, w)` — *this rule could
produce what you want* — and nothing used it. `<relevant>` turns it into a preference in one bundled
rule, so **means-ends analysis is data**, and an agent that should not prefer the rules serving its
current goal deletes it.

Two negative results, each found by breaking something, and both are the same shape:

* **Preference must order, not exclude.** Filtering recall by goal-relevance starved
  `{+blocked(heat(?a, ?w))} ⟹ {+doing(heat(anna, ?w))}` — the most useful rule in that corpus, which
  does not fit the goal at all. *Relevance to a goal is silent about everything it is not about.*
* **The apparatus is not a competitor.** Let loose over everything, preference outranked the rules
  that notice a **surprise**, so the agent pursued its goal while a channel was saying the world had
  moved. `standing` — a fact, deposited for each bundled rule — keeps the apparatus in its authored
  place. This is §19's carve-out for norms arriving a second time: *being overridable and being
  forgettable are different properties.*

So arbitration now sorts on **authority (defeat) → apparatus → helpfulness → authored order**, and
what preference replaces is worth naming: the tie among applicable, undefeated rules used to be broken
by *the order they happened to be written in*. Still total, still a lookup that never searches; with
no preferences it is exactly the authored order it always was.

**No end-to-end win yet, and the blocker is measured.** On the workload the goal still arrives at
tick 751, because:

```
  applications: bundled = 752   corpus = 64        (ask-fit alone: 711)
```

`<ask-fit>`'s antecedent is over `rule(?r)` — *every* rule — so it matches |rules|×|goals| ways and,
being standing, monopolises arbitration until backward reading is exhausted. **The phase's precedence
claim survived its deletion, as authored order**: `ugm.backward` measured "the phase starves forward
reasoning" as the phase's sin, and it moved rather than went. Fixing it is pickup item 2.

`ugm.bundle` caught `<relevant>` shipping **blind** — 15 rules, 14 exercised — before a check
existed for it. The habit earned its keep again.

### 14. Not scanning all possible options

The standing principle, stated by the user: *the system should not scan all possible options;
experience means I choose the best, or if in doubt among the 2–3 best.* §13's blocker was that
principle being violated in one specific place — `<ask-fit>` asking every rule the agent has about
every goal it holds, before doing anything.

The fix is **not** experience. It is an index:

    RuleSet.by_conclusion     rules keyed by the relation they conclude

§3 gives the substrate one index and argues for it in a line — *a rule whose antecedent names a
relation has to start somewhere, and scanning every node is the alternative.* Read backwards the same
argument holds of the rule set, and nobody had made it there. So *what could produce `w0_s8(item)`* is
a **lookup**, and `<ask-fit>` now ranges over what came to mind:

    <ask-recall>   { +goal(?w) }            =>  { +recall(?w) }
    <ask-fit>      { +recalled(?r, ?w) }    =>  { +fit(?r, ?w) }

Measured on the workload at D=8, R=8:

| | before | after |
|---|---|---|
| ticks to the goal | 751 | **57** |
| writes at the goal | 1843 | **458** |
| ticks to quiescence | 801 | **124** |
| `<ask-fit>` applications | 711 | **8** — one per goal |

Exact, not heuristic: a consequent that could produce the goal is in the bucket, and one that could
not was never a candidate. The only rules deliberately absent are those whose consequent is a bare
variable, which §12 already calls vacuous backwards and `fit` already declines.

>**An agent that has to enumerate before it can prefer has not remembered anything.** The index is
>what makes preference affordable; experience then goes on top of it — which of the candidates to
>try first, and when to stop trying.

The gap that is left is honest and small: 57 ticks against an ideal-table 8, all of it forward
reasoning in domains the goal has nothing to do with. That is now the whole of what learning has to
win, and it is the same 7× the workload's gate measures.

### 15. A preference is a score, and doubt is a tie

The user's refinement: *doubt is two or more rules scoring very close, so the table should be a
scoring and not only an order.* Right, and an order genuinely cannot say it — *one clear best* and
*two I cannot separate* look identical to a sort, and they call for opposite behaviour.

**The scale is §10's, reused rather than invented.** A `prefer` claim is an entry, an entry carries a
**grade**, and grades are the ordinal set this design already commits to. So `+prefer(<R>, k) @likely`
outranks the same claim `@possible`, and §12's weakest link applies for free — a preference derived
from a shaky premise is itself shaky, with no second mechanism to keep in step. `<relevant>` now
concludes `@possible`, because *this rule could produce what you want* is candidacy, the weakest
evidence of usefulness there is.

**Ordinal, not numeric, and that is the interesting part.** A cardinal score would be the first such
quantity in the design; §12 says ordinals do not add; and *close* would need a threshold constant
nobody could justify. Ordinals give doubt for free instead:

>**Two rules are close exactly when they tie**, and a tie needs no constant to detect.

`close(<R1>, <R2>)` is deposited when the top score is not unique — pairwise, so the arity is fixed
(§5 refuses a node whose members mean different things depending on how many there are, and *the
candidates I could not separate* is exactly the shape that tempts one).

**A tie among `standing` rules is not doubt**, and recording it buried the real cases in noise —
19 spurious pairs before the exclusion. The apparatus's order is authored on purpose (read before
acting, notice before continuing); a deliberate precedence is an answer, not the absence of one.

What is deposited and not acted on: arbitration stays total, so the choice is still made. The record
is the difference between an agent that is confident and one that merely proceeds — and what to *do*
when unsure is a claim, so it is rules, and none are written yet.

### 16. *Close* is a knob, so it is a fact — and it is numeric

The user's correction to §15: **closeness is a system knob.** Right. The first attempt got the shape
wrong and they said so — worth recording, because probing it found a defect.

That version declared pairs of grades `indistinct(certain, possible)`. Three things were wrong: it
enumerated pairs instead of saying *within N*; it was a knob on the scale rather than on the
comparison; and **it ignored half the score** — a rule scoring `(certain, 2 votes)` strictly beat one
scoring `(certain, 1)`, so the choice *was* forced, and doubt was recorded anyway.

What replaced it:

    prefer(<R>, key, 3)         the table's row: keyed on a node, matched when that key is in play,
                                carrying a SCORE
    fact +tolerance(2)          a gap of two or less is not a difference I will rely on

Applicable rows sum; two rules are close when their scores differ by no more than the tolerance. Zero
unless claimed, so the default is an exact tie and nothing depends on a constant nobody chose.

**My first version of this made ordinals add, and the user caught it.** I had the score *be* the
entry's grade, summed — which is precisely what §12 forbids, and I wrote a long apology for the
departure instead of noticing it was avoidable. The score is the **table's own cardinal**, and §10's
grades are a different scale for a different thing, untouched: an entry's grade still composes by
weakest link and no grade is ever added to another. Keeping them apart is what lets
`+prefer(<R>, k, 3) @possible` mean *a strong recommendation the agent is not sure of* — a sentence
one conflated scale would have made unsayable.

Numerals are new in the surface, and cheaply: a numeral is an ordinary atom whose **name** reads as a
number, so nothing in the graph learns arithmetic and exactly one reader wants any.

**Why it must be a fact and not a field: a rule can turn it.**

    rule <care> = implies( { +goal(doing(?p)) }, { +tolerance(4) } )
    fact standing(<care>)

An agent harder to convince when the next step cannot be taken back — *how careful am I being* is a
claim with a trail rather than a threshold somebody chose once. Checked, along with a tolerance too
small to span the gap leaving the choice decided.

**Being careful has to come before the move it is about**, and nothing orders it that way for free:
the first version of that check failed because `<care>` was an ordinary rule, so the agent committed
and *then* decided to be careful. `standing` is what says otherwise — and a corpus wants it as much as
the bundle does, so it was never a kernel/business distinction.

Two old friends on the way. `_priority` changed shape twice and a caller kept negating it as the
wrong type. And grade names were being minted with `g.atom` at the point of use — a second node with
one name, the trap this codebase has paid for four times (moot now: the numeric knob does not name
grades at all).

Also fixed while here: recall's ordering used `_rank`, which put `standing` first and filled every
shortlist with apparatus. **`standing` is a claim about precedence once a rule has matched, not about
coming to mind**; recall orders by preference alone.

### 17. Crossing opens hypotheses — and `k` is not a parameter

The user's line: *resist special machinery when the regular wrapping works; we do not need to
duplicate rules, we need a metarule to cross the `likely` and wrap back whatever we concluded — cross,
and handle on resume.* And then: *crossing a `likely` means at least one hypothesis, and two or more
if experience says so.*

That is supposing, and it is built — `<cross>` is `+likely(?p) ⟹ +suppose(?p, likely)`, and
`ugm.modality` already measures it as the winner on every axis (19 rules vs 22 for wrapping written
per-rule; works over rules with variables, which lifting does not; nests; containment structural).

What is new is the second half, and it turned out to need **no mechanism at all**:

>**There is no `k`.** The number of branches is however many `suppose` facts get concluded. Sibling
>hypotheses already work — the forest was built for them.

**Why one is the right default, as a cost:** one branch per uncertain fact is a frame per
*derivation*, which is linear and is what retired §12's *million moments* objection. Two branches make
n independent uncertainties 2^n. **The first branch is free and every branch after it is exponential.**

Two findings from building it, and they are the same shape twice:

* **The alternative must be opened ON RESUME.** Proposed alongside the first, it is enacted while
  the register is already inside it — so it nests instead of branching, and the second case comes back
  wrapped in the first. Keyed on `left(?f, ?p)` they are siblings. The callback mechanism from §5 doing
  the job that most needs it.
* **A crossing rule that can match its own output runs away** — 32 sibling frames before the budget
  stopped it, because a discharged conclusion is itself `likely(...)`. §9 records the same trap for
  `<denial>`. The corpus stops it; that it must is a property of self-applying rules.

### 18. Supposing something must not bring it about — and then nothing needs comparing

I said the gap was that nothing **compares** the siblings. The user: *why should they be compared? I
would evaluate whether one hypothesis leads to an unacceptable scenario, otherwise go on.* Right —
that is a veto, not a ranking, and it is a smaller mechanism.

But it has a precondition, and checking it found a serious bug.

**An act concluded inside a hypothesis was actually emitted.** Supposing a premise whose rule
concludes `+doing(fire(missile))` **fired the missile.** Not a leak in the chain — the conclusion
stayed inside and crossed out wrapped, exactly as §13 promises. The *boundary* was ignoring the
register: dispatch is at the write (§16) and the write never asked where it was standing.

>**§13's *nothing leaves a frame* was a claim about the chain. Effects are not in the chain.**

Fixed as a condition, not a phase: the boundary asks whether any frame on the path to the root was
entered by supposing, which the forest already records as each frame's purpose.

Also: **`doing` came out of the bookkeeping set.** Every other request stays (nothing carries a
`suppose` or a `fit` out of a frame), but *what I would do under this hypothesis* is the one thing such
a hypothesis is for — as bookkeeping, an agent that supposed a premise and found it would fire a
missile came back knowing nothing at all. What crosses is `likely(doing(...))`, which no dispatch
matches, because the boundary keys on `doing` and a wrapped intent is a claim.

**Blocking the emission was only half of it**, and the first repair stopped there — which stopped the
*reasoning* too, so a plan died at its first action. The user's correction: *actual acting should only
come out as a conclusion, a decision to act; during planning the system should ASSUME an outcome.*

>**Acting is a conclusion. What planning needs from it is the action's assumed outcome, not its
>occurrence.**

So the boundary deposits the same record under a different name — `emitted(x)` when it really left,
`taken(x)` when it was decided under a hypothesis — and one bundled row (`<taken>`) turns either into
`did(x)`, from which §15's `<assert-act>` supplies the assumption that it worked. A three-step plan
now runs to its end inside a hypothesis with nothing done at all. Note which half stays defeasible:
that the act was *decided on* is unarguable; that it *succeeded* is still `<assert-act>`, overridable.

**Substituting the action with its outcome needs no plan machinery.** One rule and one fact per
action — `{+did(?a), +achieves(?a, ?y)} ⟹ {+?y}` — and a two-step plan runs to its end inside a
hypothesis with nothing emitted, carried by the actions' effects rather than the actions.

Making the *other* half sayable (`overrides(<outcome>, <assert-act>)`, so the call is replaced
rather than also asserted) turned up something the design had assumed without providing: **a corpus
could not name a bundled rule.** Every place the docs say *a corpus can override this* depended on it
and none of it was true — the loader knew only names a corpus declared itself, so the bundle shipped
as data and was reachable only from Python. Fixed: the loader seeds its statement table from
`machine.bundle`, one namespace, so a corpus rule may not reuse a bundled name.

**One relation could not carry both intents.** `overrides` is per *step*, so `<outcome>` matching for
one action defeated `<assert-act>` for every action in that step and an undeclared act lost its
fallback. Per-*binding* does not work either — two rules bind different variables, so their bindings
cannot be lined up. Comparing **evidence** does, and it breaks the case §12 was written for:
`overrides(<why>, <boil>)` defeats a rule sharing no consumed entry with the winner, and must, because
a surprise is a rival answer to the whole situation.

| | |
|---|---|
| `overrides(A, B)` | rival answers to **one** situation — B is out for the step if A matched at all |
| `supersedes(A, B)` | rival answers to **each of several** — only B's applications sharing a consumed entry with an application of A are out |

Evidence is the comparison because the trail already records what each application matched (R5 needs
it), so nothing is measured that was not already kept. Measured: the action with a declared outcome is
replaced by it, and the action without one, in the same step, keeps its fallback.

**And then comparison is not needed.** A branch answers *does this lead somewhere unacceptable*, and
§19's veto already answers it: the hypothesis reaches the prohibition, the write is refused inside the
frame, the refusal crosses out as an ordinary record, and the branch has disqualified itself. Nothing
ranked, nothing weighed. Checked.

---

## The state of the code SUPERSEDED — see the top of this file

*(As of the previous session. Counts and the tick's shape have both changed; kept because the
reasoning around them is referenced above.)*

15 modules, ~4.7k lines. `chain` `graph` `gate` `rules` `channels` `machine` `text` are the engine;
`selftest` `agreement` `bundle` `backward` `compose` `modality` are instruments; `stratum0` is the rule-level
read.

**No phases remain.** `tick()` is recall → match → defeat → quiescence → arbitrate → apply, plus
`_leave()` when a supposition runs out of work and `_wake()` when the loop does.

**Fourteen bundled rules** ship as data (`Machine._install_bundle`): `intake`, `did`, `assert-act`,
`denial`, four `deviation-*`, `resuming`, and backward reading's `ask-fit`, `plan`, `expand`,
`ask-check`, `give-up`.

**Five write-time hooks**: `_dispatch` (acting), `_enter` (supposition), `_fit`, `_settle`,
`_verdict`. These are Python callables, which is honest debt — §21 records it.

**One veto**: `_forbid`, §19's carve-out. Not a hook and not a rule — it runs *before* the deposit,
which is the whole of its guarantee.

---

## Where I would pick up SUPERSEDED — see the top of this file

*(The previous session's list. Item 1 is **done** — `enough`, `stopping`; two of its four hats are
answered and two remain, carried forward. Item 2's ordering trap is answered by forgoing. Item 3 is
**done** in outline — `review`/`blame`/`learned`, though the arena it measures in was the real
finding. Items 4 and 5 stand. Kept for the arguments, not the priorities.)*

**1. A reason to stop.** The measurement that makes this first: an *ideal* recall table reaches the
goal in **8 ticks instead of 734**, and makes no difference at all to a run that goes to quiescence
(§12). Recall's prize is real and uncollectable. Learning, the composition trigger, and any claim that
an agent is efficient are all waiting on this — not on a bigger corpus.

It is one question wearing four hats, and they should be answered together or not at all:

* when is a plan **settled**?
* when is a `due` rule **done**?
* when may a request be **re-asked**? (§10 — a request is a fact, so it can only be made once)
* when may a binding be **reconsidered**? (§21's backtracking; `_settle` never returns to one)

**2. Acting on doubt before committing.** §15–16 built the noticing — `close(<R1>, <R2>)` when the
choice was not forced, `tolerance(n)` as the knob a rule can turn — and deliberately not the response.
Think longer, ask a channel, suppose one and look, prefer the reversible move: all claims, so all
rules, and none written. The ordering trap: arbitration is total, so **the move is already made when
the doubt is recorded**. Deferring it needs the same missing thing as item 1.

**3. Experience.** §14 removed the enumeration; what is left is genuinely recall's job and nothing
does it — *which candidate to try first, and when to stop trying*. `prefer` is derived from `fits` or
authored, never learned. The user's standing view: **learning is offline, not online** — credit needs
the outcome, and the outcome is not known until the episode ends. `quiet` is this engine's *episode
over*, and it is the same occasion that makes `blocked` legitimate. Before building it, check what
the trail can actually support: `achieved` is written for very few goals in a workload run, so
outcome-based credit has thin evidence today.

**4. The composition trigger.** Composition is built and measured (n steps → 1, defeat inherited).
Missing is *when*: §4's `compose what has run often and never surprised; decompose what surprises`,
neither half wired. `RuleSet.composed_from` records what each shortcut collapses, so decomposition
knows where to look. Trained by the same signal as item 3.

**5. Grades are not in the graph.** `chain.py` says grade, licence and source are *"ordinary facts
about the entry (§5)"*. They are not — they are Python fields on the `Entry` tuple, so **no rule can
read a grade**, which is why `ugm.modality` reports *a rule cannot ask whether something is merely
likely*. One deposited fact per entry would close it.

**Smaller, well-specified:** lifting a modality across a rule (the last caller of §5's wall with no
service); a seat move is not yet an entry (§17 says every seat move is a write); write-time hooks are
not rules; what a `?` conclusion becomes on the way out of a supposition (§9); whether a channel
reporting a denial should write `says(c, p, -)` or `says(c, not(p))`, and whether permitting both
splits a corpus into dialects; the transpiler sketch in §21.

---

## Two habits worth keeping

**Every gate must delete each rule of the thing it checks, one at a time, and report any rule the
fixture cannot kill.** `ugm.agreement` reported success three times while unable to fail — a revision
written at the wrong locus, a read silently picking the first candidate, a transitive rule needing a
*non-competing* entry in between. `ugm.agreement`, `ugm.bundle` and `ugm.backward` all do this to
themselves now, and it has caught something every single time.

**Commits**: sole author, short lowercase topic word, and **never** a `Co-Authored-By:` or
`Claude-Session:` trailer. Audit with `git log --all --format='%B' | grep -ci claude` — it must
return 0. It does.

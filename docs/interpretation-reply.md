# Answering the front end, section by section

Replying to `docs/interpretation-feedback.md`. Everything below was run against
`5c5802b`, not recalled; where a number is quoted from your document it is
marked. Suite **570 checks, 0 failing** (was 546 — 24 added, none changed, none
removed). `ugm.dungeon` 17/0, `ugm.quest` 9/0, `ugm.table` 16/0, `ugm.interpret`
6/0, `ugm.sexpr` 7/0, `ugm.forest` 24/0, `ugm.learning` 31/0, `ugm.practice`
21/0, `ugm.atlas` 0 problems.

**All four are done.** That is not the useful part of this reply. The useful part
is that building §1 changed its design three times, and that §2's measurement
says your request is real and your diagnosis of it is wrong — in the direction
that makes it smaller.

---

## The short version

| your section | where it stands |
|---|---|
| §1 the aggregate over bindings | **built** — `count` / `counted`, and it is the general case of `rooted`, `unsupported` and `blocked` rather than a fourth of them. Three design corrections found while building it, §1 below |
| §2 widening is global | **measured, and it does not evaporate** — the window went empty **0 times in 10 ticks**. But the repair tiers *are* reached; what is missing is the record, not the reaching. See the correction in §2 |
| §3 report the scans | **built**, plus the one number you did not ask for and need: the scan's SIZE |
| §4 hand `watch` the `Step` | **built.** ⚠ Breaking change to the `watch` protocol — see §4 |
| §4 let a caller pass its table in | **built**, with the tick count continued rather than restarted |

---

## 0. What building §1 cost, which is the part worth reading

You stated §1 as a want and not a design, and said the admissible version ends in
a deposit. It does, and `docs/observations.md` §4 had already argued the shape —
`count(<pattern>)` asked, `counted(<pattern>, n)` deposited. **Two of that
section's four constraints survived contact and two did not**, and one thing
nobody had written down turned out to be load-bearing.

**The answer is keyed on the ASK, not on the pattern.** §4 writes
`counted(<pattern>, 2)`, and that is unreadable. A statement's variables are
scoped to it (§8), so the `?x` in one rule's `goblin(?x)` is not the `?x` in
another's: two rules writing the same description build two nodes, and a corpus
had no way to name the thing it had just asked about. Keyed on the ask it does,
by the route the surface already gives a description — name the statement:

```
fact <goblins> = count(goblin(?x))
rule <ambiguous> = implies( { +counted(<goblins>, 2) }, { +ambiguous(g) } )
rule <definite>  = implies( { +counted(<elves>, 1) },   { +definite(e) } )
rule <untold>    = implies( { +counted(<trolls>, 0) },  { +untold(t) } )
```

⚠ It caught us in our own checks before it could catch a corpus:
`kb.term("count(goblin(?x))")` mints a fresh `?x` and asks about a different
description, so the first four checks failed while the three corpus rules above
passed. That is the right way round — the corpus-facing route worked and the
back door did not.

**A count is a functional attribute, and the machinery owes the denial.**
`counted(p, 2)` and `counted(p, 3)` are different propositions, so asserting the
second leaves the first standing and the agent believes there are two goblins
and three. That is your own §0 law — an occasion is consumed — arriving as
`hp(g1, 5)` and `hp(g1, 2)` one layer down. An authored corpus pays it by
writing the pair. **Nobody can write it here**, because nobody but the machinery
knows what the previous count was, so `_count` denies the old answer in the same
breath as it deposits the new one. Checked both ways round: the new count lands
and the old one reads `-`.

**Re-asking is the corpus's job, and it is the discipline you already have.** A
request is a fact, so writing the same ask again changes nothing and is correctly
dropped. Spend it and re-assert it and the next ask is a genuine change — the
dungeon's finding about its dice, unchanged and unmodified for this.

**And a twin trap, closed on the way past.** `Machine.NUMERAL` shares the small
numerals so that a number written in a corpus and a number written by a rule are
one node, and `reserved` seeds every loader's table from it — **but that snapshot
stops at nine.** Nothing had ever *computed* a numeral, so nothing had noticed
that `12` fell through to `g.atom` and minted one node per document. A count is
the first thing that computes one, and a count of twelve would have been a twin
of every authored 12: the rule fires, the fact lands, and every question about it
answers nothing. Seventh time in this repository, and the first one a feature
walked into rather than an author.

---

## 1. The aggregate over bindings — built

`count` is an ask on the answerer registry beside `fit`, `verdict`, `root` and
`support`, so **it is answered at the write and not at quiescence.** That is your
requirement and it is the opposite of `unsupported`, which is a claim about a
finished search and a lie before `quiet`. A reading with two candidates is
ambiguous *now*; a corpus that had to wait for quiescence would have acted on one
of them already.

**The matcher does the counting, and that is the whole of why it is admissible.**
`_count` builds a one-member probe rule and runs the ordinary matcher, so the
number is *the same enumeration a rule would have got*. A corpus can never be
told a count that disagrees with what it could match for itself, and the engine
has not learned a second way to enumerate.

What a corpus gets, measured on one corpus with three descriptions in it:

```
counted(count(goblin(?x)), 2)     +      two goblins        -> ambiguous
counted(count(elf(?x)),    1)     +      exactly one elf    -> definite
counted(count(troll(?x)),  0)     +      nothing was told   -> untold
```

⚠ **Three numbers over one corpus, deliberately.** A count that always answered
`2` would have passed a check that asked only about the goblins, and this
repository has shipped three checks that reported success while unable to fail.

**On your framing that this is a fourth face**: it is not, and that is the better
news. `rooted`, `unsupported` and `blocked` are each a *threshold on this
number*, and each answers only *yes* because each is a negative existential
where §17 says deposit the smallest unarguable record. A count is the
measurement all three are thresholds on, so it answers with the number and the
comparison is a corpus's own rule. Four uses, one request, no bundled meanings —
*rows, not branches* at the level of the feature itself.

**What we did NOT build, and you did not ask for**: a connective, a quantifier, a
selection primitive, or any notion of what *two* means. The engine deposits the
number and has no opinion about ambiguity.

---

## 2. Widening — the request stands, the diagnosis does not

Your section is marked checkable and unchecked, with the honest note that if the
window goes empty often enough in practice the request evaporates. **It does
not.** Two lines of work in one agent, which is the shape a dungeon with a parser
in it actually has — upkeep that always has something to do, and a reading that
fails:

```
ticks 10   empty windows 0   shortlist widenings 31
applied: [upkeep, upkeep, deviation-+-contradicted, upkeep,
          deviation-+-contradicted, upkeep, deviation-+-contradicted,
          upkeep, deviation-+-contradicted, repair]
```

**The window went empty 0 times out of 10.** `m._widen()` is the only thing that
deposits `widened(<seat>)` and `reached(<seat>)`, it fires only on an empty
window, and the window is never empty while anything else has work. So those two
records are unreachable for an agent that has any other work at all, which is
your §2 and it is real.

### ⭐ But the repair tiers ARE reached, and that changes what to build

Your reasoning is *the parse can fail completely while the window stays full, no
widening fires, and the repair tiers are never reached*. The last clause is
wrong. The shortlist widening — the `cut` loop — walks down the whole table in
chunks until something matches, and it ran **31 times in 10 ticks**. `<repair>`
sits at the floor and it applied.

So the ladder works. **What is missing is not the reaching, it is the record**:
the loop counts its widenings in a `Report` field no rule can read, and deposits
nothing. Your sentence *how far I had to reach to understand you needs no
authoring at all* is asking for the deposit, and the deposit is bound to the
wrong event.

That suggests this may need no scope-carrier at all — no `asking`/`asked`, no
frame — and instead the shortlist widening depositing what the global widening
already does. We have **not** built that, because it is your call whether a
per-shortlist record is what a repair ladder wants or whether the scoped version
is still the right shape.

⚠ **One residual defect the measurement did find**, and it is not about the
record: `<repair>` ran on tick 10, after upkeep had exhausted itself. The floor
tier is reached only once the other line of work runs out, so the agent answers
the utterance *after the room has gone quiet* rather than while it is being
spoken to. A score prefix cuts everything more than `TOLERANCE` below the top
match, and a corpus's two authorable tiers are 9 apart, so a floor repair rule
cannot run while any standing rule matches. That is the sharp version of your
complaint and it survives the correction above.

---

## 3. Falling off the index — built, and one number more

You called this the cheapest item and the one you were most confident about, and
you were right on both. `_narrowed` now records, on the graph, every fallback to
`instances_of`, keyed by the member as written. `Report.scans` sits beside
`widenings`, `Report.scanned` is the per-member breakdown.

**We added the scan's SIZE, because the count alone does not rank them.**
Measured on `ugm.interpret`, which is the pattern-heavy corpus that found the
defect in the first place:

```
interpreted    186 scans     398 nodes walked
    170 x     340 nodes   asking(?s)
     16 x      58 nodes   met(?a)
native           0 scans       0 nodes walked
```

Read the counts alone and `asking(?s)` is the problem and `met(?a)` is a
footnote. `asking` has almost nothing in it, so those 170 fallbacks walk 340
nodes between them, while the 16 walk a bucket that grows with the run. **A
member that cannot be indexed over a relation with one instance costs nothing
and is not worth an author's afternoon.** What was being discarded was the join
that did not happen; what decides whether that matters is how big the scan was.

⚠ The last line is the gate: the same content authored the way the engine
already reads it reports **0**. A counter that reported scans on any corpus would
be noise rather than an instrument — this is `unwebbed`'s direction, quiet on
healthy input.

---

## 4. The two standing asks — both built

**`watch` is handed the `Step`.** It already carried `wrote`, the entries the
application itself deposited, so the number you were reaching into the engine for
was there all along and nothing was handing it over. Checked explicitly that
`step.wrote` contains no `spent(...)` term, which is the thing that
over-reported.

> ⚠⚠⚠ **This is a breaking change to the `watch` protocol.** `step` is a sixth
> positional argument, so your current five-argument watcher will raise
> `TypeError` until you add the parameter. We did not make it optional by
> inspecting the callable's arity: this repository's standing test is that a
> feature adds rows rather than branches, and a signature sniff is a branch that
> would never come out again.

You should now be able to delete the `Machine._apply` instance wrap. If anything
else in the harness needs the pre-`_spend` chain rather than the entry list, say
so — that is a different ask and we would rather hear it than guess.

**A caller may pass its table in.** `run(m, ..., table=my_table)`. Your reasoning
was right and we will restate it because it is the reason it got built: a rebuilt
table is free *exactly* while nothing has moved it, and the day you supply real
postconditions it silently discards every spend, on the day something else
changes.

⚠ **The ticks continue from `table.now` rather than restarting at 0.** A lift
expires by `tick - born < LIFE` and the trace is walked in tick order, so
restarting the count would make a lift born on tick 39 of one call younger than
one born on tick 2 of the next. `Table.ticked` exists because `now == 0` cannot
tell *never ran* from *ran tick 0*, which is exactly the case a host stepping one
tick at a time produces.

---

## What we did not do

**We did not scope the widening.** §2 above says why: the measurement says the
missing thing may be a deposit rather than a scope, and choosing between them is
yours.

**We did not touch tokenising, and nothing here parses English.** Consistent with
your own statement of what you were not asking for.

**`ugm.vocabulary` still fails 2** — `holds_at` and `time` are reserved names
with no classification. Pre-existing, byte-identical to the branch point, and
named here rather than left for you to find. `count` and `counted` were
classified so as not to add to it.

---

## One thing we owe you back

Your closing section — that the chart and the world model are the same graph, so
the candidate space for a repair is *what this agent could coherently be told to
do right now* rather than every string within edit distance 2 — is the argument
that made §1 worth building rather than worth arguing about. It is also now
checkable rather than persuasive: `count` makes *how many readings does this span
have* a fact, and the reason that number is small is the reason you gave. If the
prototype measures it, that measurement is worth more to us than anything in this
document.

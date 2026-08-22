# What a language front end would want, and what it would not

From the harness side, at `harneskills@a9b1e6d`, against `ugm@907e6c9`.

 **Nothing below was measured.** `dungeon-feedback.md` opens with *everything
below was run, not recalled*, and this file cannot make that claim: it is
reasoned from `docs/observations.md` §2.18–§2.23, `ugm/attention.py`,
`ugm/rules.py` and `ugm/interpret.py`, plus two standing asks from the harness's
own handoff. It is a request list, not a report. Where a claim is checkable and
unchecked, it says so.

The occasion is a design conversation about ingesting an **utterance as
word-atoms** — one fact per word, adjacency as a fact — and letting rules read
it, rather than handing the machine a term some Python already built. §2.19
established the half after that step (*one rule per constructor*, measured,
accountable via `why`). These are the four things the half **before** it runs
into.

---

## 1. The aggregate over bindings — a fourth face, and the reason it stops being a tail case

§2.23 already names this as the one mechanism worth building for the whole
document, with three faces:

| | |
|---|---|
| §2.6 | *nothing was told about this* — a negative existential |
| §2.12 | *held at every moment of this stretch* — a universal |
| §2.23 | *exactly one thing satisfies this description* — uniqueness |

**A fourth: *the cheapest derivation*.** Error-tolerant parsing (Aho & Peterson
1972) works by adding **error productions** — insert a token, delete one,
substitute one — each carrying a cost, then taking the minimum-cost derivation.
Costs sum **across a derivation**. The attention table ranks rules, one at a
time, so it can order *kinds* of repair and cannot compare *totals*: two cheap
repairs against one expensive one is not a question a per-rule score can be
asked.

⭐ **What we want to add is not the fourth face. It is that parsing moves this
whole family from the tail to the common case.** In §2.23 the double attack was
an adversarial probe — *attack the goblin that attacked you three turns ago*,
constructed to break something. In a grammar, two readings over one span **is
what ambiguity means**, and it happens on ordinary input, from ordinary people,
every few sentences. §2.23's own verdict on that failure was *silent, and
actionable*, and §19 says an emitted act cannot be forgone. A front end that
repairs structure makes that the normal path rather than the probe.

**The shape we would want, stated as a want and not a design.** Per
`deposit-dont-decide.md`, the admissible version ends in a deposit: how many
bindings satisfied a member is something **only the machinery can know**, and it
is one fact and no interpretation — the same standing as `widened`, `quiet` and
`bounded`. What a corpus does about *two* is then a rule, which is where the
decision belongs. We are not asking for a connective, a quantifier, or a
selection primitive.

---

## 2. Widening is global, and graceful degradation wants it scoped

`attention.py:707` — widening fires when **`if not window`**: nothing in the
score-ordered prefix matched, anywhere. The comment on the deposit is the reason
this looked so promising from here:

> `widened(<seat>)`, `reached(<seat>)` — so *I had to go and get that* is a
> sentence a corpus can write.

That is exactly the record an error-tolerant parser wants, for free. The
intended use is a score ladder:

| score | rules |
|---|---|
| `standing` | exact lexicon, exact grammar |
| middle | morphology, synonyms, abbreviations |
| floor | one insertion or deletion; guess from what is standing in the world |

Clean input never matches a repair rule, because the window is never empty.
Broken input walks down one tier at a time and each step deposits its own
record, so *how far I had to reach to understand you* needs no authoring at all.

 **And we think it does not work, for a reason that is not the ladder's
fault.** The window is empty only when **nothing anywhere** applies. A dungeon
has upkeep, monsters with turns, and standing policy; something is almost always
applicable. So the parse can fail completely while the window stays full, no
widening fires, and the repair tiers are **never reached** — with no report,
because from the loop's side nothing went wrong.

**The ask, in one sentence: a way to say *this line of work found nothing*
rather than *the machine found nothing*.** We have no proposal for what carries
the scope — `asking`/`asked` and the frame both look like candidates from here
and we have not tested either.

 Checkable and unchecked. It is the **first** measurement the prototype would
make, and if it turns out the window does go empty often enough in practice,
this request evaporates and only §1 remains.

---

## 3. Falling off the index is silent, and a grammar is where that bites

`_narrowed` now skips a structure that still carries a variable and falls back
to `instances_of` — correct, and better than the defect its docstring records
(the bucket for `said(implies($a, $c))` is empty, so the member matched
**nothing**, with no error and no scan). The docstring is right that the
fallback cost is one the function already sanctions.

But the fallback is **also silent**, and a grammar is the corpus that changes
the stakes: hundreds of rules whose members are pattern-heavy by construction,
where the difference between a bucket and a scan is the difference between a
parse and a hang. Today an author cannot tell which one they wrote.

**Ask: report it.** `Report` already carries `widenings`; a `scans` counter
beside it would be enough to see it, and a per-rule breakdown would be enough to
fix it. This is the cheapest item on the list and the one we are most confident
about, because it needs no design decision — the information exists at the point
where it is discarded.

---

## 4. Two standing asks from the harness, filed here because this is where they belong

Neither is new and neither is about language. Both are starred in
`harneskills/docs/HANDOFF.md`, which is not a file this repository reads.

**Hand `watch` the `Step` the loop has just appended.** By the time `watch`
runs, `_spend` has appended its refraction bookkeeping, so *entries since the
choice* over-reports by a `spent(...)` term longer than the line it sits on —
measured on the harness side, not assumed. The harness therefore wraps
`Machine._apply` **on the instance** for the length of a run. That is the only
place the harness reaches inside the engine, and one line upstream removes it.

**Let a caller pass its table in.** Rebuilding the table per `/step` is free
today, because with no postconditions supplied a table is its defaults plus a
`prefer` lift recomputed from the graph every tick — a rebuilt table is the same
table. The day the harness supplies real postconditions, `/step` silently resets
what the agent learned within a run. Silent, and only on the day something else
changes, which is the shape worth pre-empting.

---

## What we are **not** asking for, stated rather than left to be inferred

**Not natural language in the engine.** §4 of `observations.md` says turning an
utterance into structure is an interpretation, so it belongs to a tool or a
corpus and never to the floor. We agree, and everything above is consistent with
it: the requests are about *reading a fact-shaped utterance*, not about parsing
English. Tokenising stays outside.

**Not weights, grades, or costs back on the surface.** Removing `@certain` was
right, and the ordinal table is a better fit for repair than probabilities are —
what a repair ladder needs is an **ordering**, which exists, not a metric. The
gap in §1 is the aggregate, not the number, and adding numbers would not close
it.

**Not an index bucket for a variable relation.** §2.19 flags `$r($x, $y)` as the
one real limit, but §2.23-B then writes `$v($whom, $kind)` and it emits
correctly — unindexed, and working. §2.19's own suggestion that command forms
are a much smaller open class than concepts looks right to us, and a row per
form looks like the answer rather than the limitation. Item §3 above is the
version of this we do want: not a bucket, just being told when there is none.

**Not a repair mechanism.** Error productions are rows, and §20's test passes on
them — a new repair form is one more rule, not a branch anywhere in Python. The
engine should not learn what a typo is.

---

## The one thing that made this look worth doing at all

Recorded because it is an argument in the engine's favour and those are worth
writing down too.

"Closest **meaningful** structure" hides two questions — closest that *parses*,
and closest that *makes sense in the world right now*. Conventional pipelines
are good at the first and bad at the second: parse, then filter, then discover
the winning parse was absurd, with no cheap way back.

Here the chart and the world model are **the same graph**. §2.19's `<i-pick>`
already rejects `rat_c` mid-reading because the rat is not a goblin — a KB fact
consulted *during* the parse rather than after it. So the candidate space for a
repair is not *every string within edit distance 2*; it is *what this agent
could coherently be told to do right now*, which is small, and is already
deposited. `attack the door` parses perfectly and is nonsense; `atack gobln` is
garbage with exactly one sensible reading when one goblin is standing.

That property gets **stronger** as a corpus grows, which is the opposite of how
a bolted-on semantic filter behaves, and it is the reason this is being asked
about here rather than solved with a parser.

# Learning

Everything up to here takes the rule set as given. A corpus is authored, the
bundle ships, and the agent's cleverness is entirely in what it does with what
it was handed.

This chapter was written to be the other half — Part 2's claim taken
seriously:

> **A rule is a node. So a rule can be the conclusion of a rule.**

That claim is still true: `reify` (Chapter 10) makes every rule's antecedent
and consequent ordinary readable structure, `rule($r)`, `ant($r, ...)`,
`con($r, ...)`, the moment the rule is authored. What follows is a different,
more honest chapter than the one this replaces, because the three mechanisms
it was built to describe — composing a derivation into a rule, an agent
adopting a rule a corpus concluded, and learning a rule from two examples by
anti-unification — do not exist in the engine as shipped today. They were
built, they lived in a package called `ugm/learning/`, and that package was
deleted in the same restructuring that replaced the chain of moments with the
scratchpad (Part 1's basic chapters): "goal management, the vetoes, attempt, again, the
call stack, the premise economy, the act vocabulary, expects, and all of
learning — which comes back on a memory system rather than on a history the
engine keeps by accident," in the words of the commit that did it. Nothing
currently in `ugm/core/rules.py` or `ugm/core/machine.py` composes, adopts, or
anti-unifies anything, and no corpus in this repository builds one.

What survives is the argument for why each piece would have to work the way it
did, which is worth keeping — the book already narrates *built, measured, then
removed* as a first-class device — and the one piece of the chapter that is
still real: a corpus can attend a node in response to what just happened, and
that alone is enough to shape the table (Chapter 28) without anything called
"learning" at all. The gap is tracked honestly in
[`../horizon/34-not-built.md`](../horizon/34-not-built.md).

## Three ways a rule was meant to get made

### Composition — collapsing a derivation

The idea: having derived `e` from `a` by way of `b`, `c` and `d`, mint the rule
`a → e` and use it directly next time. Measured at the time, over a chain of
length *n*, *n* steps became one, for any *n*, with the same conclusion — and
the distinction from compilation was the chapter's sharpest point, and still
is, as a design argument:

| | **compilation** | **composition** |
|---|---|---|
| produces | a host-language artifact | **a rule — an ordinary node** |
| reduces | the cost of one step | **the number of steps** |
| the gain | a constant factor | algorithmic |
| inspectable | no | yes |
| lives | outside the graph | in the graph |

> **Compilation makes a step cheaper. Composition makes the step unnecessary.**

A composed rule, had it shipped, would violate nothing: data, askable,
attributable, defeasible like any other rule. Two things it would have had to
inherit: a constituent taken out of the running (`dormant`) takes the
composition with it, and a guard is inherited for free because composition
takes the union of the antecedents. And composing across the old `causes` was
refused, because a `causes` step read its other premises one moment later than
an `implies` step, and flattening lost conclusions — moot now that `causes`
itself is gone.

### Adoption — a rule concludes a rule

```
adopt(<R>)
```

The idea: a corpus concludes `adopt($r)` and the named rule goes live, with two
constraints found while it was being built. **Refused inside a supposition** —
a frame's conclusions are unreadable from outside by construction, but the
rule set would have been one list shared by every frame, so adopting inside a
hypothetical would have applied the rule after the frame discharged, to
everything, which is exactly what supposing must not do. And **the adopted
rule must be the node the graph describes** — minting a fresh one makes the
live rule a twin of the described one, a defect this project's own history
calls the **twin trap** and had found seven separate times by the time this
chapter was written:

> **Anything that binds a name has to go through the table that resolves it.**

Neither constraint is exercised by anything today, because there is no
`adopt`, and — see Chapter 25 — no supposition either. `ugm/core/attention.py`
still has a comment about what `adopt` would mean for a table (`Table.absorb`
exists to take in "rules the agent did not start with"), which is the one
trace left of the feature in the current source.

### Learning from examples — anti-unification

The idea: given two things that happened, what pattern do they already agree
about — the dual of unification:

| operation | asks | answers with |
|---|---|---|
| **match** | does this pattern fit that thing? | a substitution |
| **unification** | can these two patterns be made the same? | a substitution over both |
| **anti-unification** | what do these two things already agree about? | **a pattern** |

The argument that made it learning rather than noise was **one mapping across
premise and conclusion** — generalising the premise and the conclusion with
separate dictionaries gives a rule whose conclusion mentions things its
premise never bound, which is either vacuous or wrong. And it would have
needed to **decline** when two examples share no structure, rather than return
something vacuous — a difference against nothing is not a difference. None of
this is implemented; `ugm/core/rules.py` has no anti-unifier, and nothing
calls one.

## Why a corpus can't write a rule's insides itself, even today

This part of the argument doesn't depend on the missing tool, and it still
holds: a corpus cannot write a new rule's insides *as ordinary surface text*,
for three reasons that are still enforced. A `fact` may not contain a
variable, so a corpus cannot write a rule's patterns that way. A statement's
variables are scoped to it, so parts written on separate lines could not share
a `$x` even if a fact could carry one. And a rule's consequent may carry only
variables its antecedent binds — a rule being *built* has no antecedent yet.
So the corpus never names the new rule's insides; it would have to reach them
by **binding** — *reference is binding*, arriving where it would have been
load-bearing. Composing a rule, or learning one from examples, would have been
a function, and a request answered by a function is a **tool** (Chapter 22) —
had either shipped, it would have had to ship as one, for the same reason
`kb.answerer`/`kb.computator` exist at all.

## The one input that still works: a prediction that failed

Composition needed a derivation and anti-unification needed two examples. Both
start from something that went **right**. The third input was one an agent
produces by itself, for nothing, every time its model of the world is wrong —
and unlike the other two, the *apparatus for noticing it* is buildable today,
in ordinary rules, as Chapter 25 shows:

```
fact +heating(k1)     fact +contains(k1, water)
fact +heating(k2)     fact +contains(k2, sand)

rule <boils> = implies(
    { +heating($k), no boiling($k) },
    { +boiling($k), +expects(boiling($k), plus) } )

rule <trust> = implies( { +says($ch, $p), no $p }, { +$p } )

rule <deviation> = implies(
    { +expects($p, plus), +not($p), no deviates($p) },
    { +deviates($p) } )

say world: +not(boiling(k2))
```

```
kettles.ugm: 8 ticks, ended quiescent

what it believes, newest first:
  deviates(boiling(k2))
  not(boiling(k2))
  expects(boiling(k1), plus)
  boiling(k1)
  expects(boiling(k2), plus)
  boiling(k2)
  says(world, not(boiling(k2)))
  arrived(world, not(boiling(k2)))
  contains(k2, sand)
  heating(k2)
  contains(k1, water)
  heating(k1)
```

A real corpus's rules are rarely wrong in exactly this way, which is why
`dungeon` — this project's larger fixture, where the game's own rules are
never wrong — finds nothing to be surprised about; a kettle whose gauge
disagrees with the causal story is the fixture built to have something to
find.

What a learner would need is on that belief set, and none of it needed special
instrumentation to be there:

```
which prediction failed      deviates(p)
about what                   the members of p
and what did NOT fail        the same relation, holding, about something else
```

`which rule made the prediction`, though, is **not** recoverable from this —
that is exactly the support-trail question the scratchpad collapse traded
away (see this chapter's opening note). `expects(boiling(k2), plus)` is on the
record; which rule wrote it is not, unless the corpus itself deposits that too
(`+licensed_by(expects(boiling(k2), plus), <boils>)`, say — an ordinary fact,
nobody's business but the corpus's to write).

> **A belief set kept for reasoning is not automatically a training set.** It
> tells you *what* is believed. Anything that would have needed *why* has to
> be written down by the rule that concludes it, on purpose, as data.

### What a discriminator would have looked for

The idea, restated rather than run: abstract every fact about the failing
subject by replacing the subject with a hole, do the same for a subject the
rule got right, and subtract.

```
k2 (failed)      heating(_), contains(_, sand)
k1 (succeeded)   heating(_), contains(_, water)
difference       contains(_, sand)
```

`heating(_)` is true of both, so it discriminates nothing — and it's the
premise `<boils>` already has; a learner proposing the rule's own premise
would be proposing noise. And with nothing to contrast against, it would have
had to decline, for the same reason anti-unification would: a difference
against the empty set is not a difference.

What it would have emitted was one ground fact —

```
fact +likely(prevents(contains(_, sand), <boils>))
```

— ground, because a fact may not contain a variable, so the candidate names
the distinguishing **argument** rather than a pattern. This much (writing
`+likely(...)` as an ordinary consequent, wrapped rather than fighting what
the agent was told) any corpus can still do by hand today; what's missing is
the machinery that would have proposed it automatically.

### The ontology, and why it mattered

One lesson from one failure does not generalise, because it does not survive a
second example. Two kettles fail — one of sand, one of gravel — and the raw
contrast gives two answers with nothing in common. With the corpus's own world
model consulted (`is_a(sand, solid)`, `is_a(gravel, solid)`), the design's
argument was that every feature should be offered abstracted as well as raw,
so the two failures share exactly `contains(_, :solid)`:

> **The ontology is not decoration. It is the difference between a lesson
> about a thing and a lesson about a kind** — and therefore between memorising
> and generalising.

That argument doesn't depend on the missing implementation to be sound; it's a
claim about what *any* such learner would need, restated here because the
chapter that made it no longer has code behind it to point to.

## What a learned rule would conclude

This part needed nothing new, and still needs nothing new if it's ever
rebuilt: a learned rule concludes **wrapped**, `likely(p)` rather than `p`.

> **A rule that concludes wrapped cannot fight what the agent was told.**

`likely(p)` and `not(p)` are not rivals; they're different claims, and a
corpus that wants to act on the first has to cross that line deliberately
(Chapter 16). Any corpus can write `+likely(...)` today — nothing about this
convention was ever engine machinery, which is exactly why it's the one piece
of this chapter's apparatus a corpus author can still follow.

## Retiring is not defeating

One distinction worth keeping regardless of what learns the lesson:

> **Losing an argument is not being wrong.**

A rule that is right about a thousand cases and loses to a more specific one in
five is not a bad rule. Retiring it because it lost throws away every case it
was right about. So nothing should retire a rule on the agent's behalf. What a
rule keeps losing to is a corpus's decision to notice and act on: ask its
author, add the premise that tells the two apart, or mark it `dormant` —
which is a claim, and `due(<R>)` (Chapter 27) takes it back.

## Experience: where the table's numbers come from, today

Chapter 28 left one thing open. The postconditions are *what a learning
process calibrates* — so what, currently, is the learning process?

### 1. Being taught — the residue of ordinary use

Not a labelling task run beside the system: the ordinary first use of a
corpus, by a person who steps it and picks the next rule, doing exactly what
the table will later do — so what they leave behind *is* the table. `attend`
is what a lesson spends, and it's a lesson conditional on the rule that just
ran, not a flat opinion about a rule in general:

```
learned after <move> { +covered($d) } => attend($d, 3)
```

Run for real:

```
learned.ugm: 2 ticks, ended quiescent

what it believes, newest first:
  covered(orc1)
  wounded(orc1)
  enemy(orc1)
```

— the `learned` keyword marks the trigger's spend as something a calibration
process, not the corpus's ordinary logic, put there; `frozen` marks the
reverse, what calibration may not touch. Both are read by
`ugm/core/text.py` and both are current. A lesson names a **thing**
(`attend($d)`), never a rule — a lesson against a rule id goes stale the
instant a rule is adopted, composed or renamed, which is one more reason those
mechanisms staying unbuilt hasn't cost this convention anything: it never
depended on them.

### 2. Reviewing — offline, and it is a corpus

The idea: an episode ends, the trail is walked, what was learned is written as
surface text the next episode loads. This one is harder to certify today
specifically because "the trail is walked" is the support-trail question again
— what's walkable now is the belief set, not a derivation. A corpus can still
write `learned after` lessons by hand from reading a transcript; whether that
process can be automated the way it originally was is exactly the gap this
chapter's opening note names.

### 3. Practising — goals the agent sets itself

The idea: read a corpus's own `achieves` facts backwards and let the agent
propose its own practice goals inside a **supposition**, so a bad route costs
nothing rehearsed. This one depends on the piece that's most completely gone:
there is no `suppose`, no `doing`/`taken` distinction, and no boundary that
keeps a rehearsed act from landing as a real one. `ugm/core/attention.py`'s
`run()` still accepts a caller's own frame and floor — the raw capability to
nest one run inside another without popping past the caller exists — but
nothing in the surface exposes it as a corpus-authored supposition. Filed
where the rest of this chapter's gaps are filed:
[`../horizon/34-not-built.md`](../horizon/34-not-built.md).

## Where this stands, honestly

The instrument that used to gate this chapter — teach a table from one
demonstration, compare it against the uncalibrated table on the same corpus —
was itself part of what the restructuring removed, so its numbers are history
rather than something this rewrite re-ran. What the earlier version of this
chapter found, kept here because it's the right note to end on rather than
because it's freshly measured: **calibration is easy to build and hard to
show actually helps**, and a corpus with nothing to teach cannot measure a
teacher, which is the same shape as Chapter 18's census finding. The
`chooser` argument `ugm.core.attention.run` still takes — a human, or any
other policy, may pick from the window instead of the table's own top choice
— is real and current; nothing currently plugs a calibration process into it
in this repository.

!!! note "Deep dive: a gate that crashes reports the same thing as a gate that passes"
    The earlier version of this chapter reported a gate that raised on its
    first corpus and never measured the second — silent in the worst way, a
    check that could not *finish* rather than one that could not fail. Kept
    here as the general lesson, independent of the specific gate: a
    comparison you have not re-run recently is a claim you are making on
    faith, and this chapter tries hard not to make any more of those than it
    has to.

---

That's Part 6. Parts 7 and 8 are the last two, and they go underneath.

**Next:** the five things that genuinely could not be taught.
[What cannot be a convention →](../floor/30-the-floor.md)

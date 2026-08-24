# Zero phases

Chapter 30 stated a test with a falsifiable consequence:

> **The interpreter's step should have no phases.**

Match, commit, write — and everything else a corpus wants becomes rules that
those apply. The count of phases is a direct measure of how much of the taught
layer has escaped onto the floor, and it's a number this chapter can print.

It prints **zero**.

The step is: score → take the first rule in the window whose antecedent
matches → apply it → spend its postconditions. Plus widening when the window
runs dry, and ending when a rule spent `stop`. `ugm/core/attention.py` states
this as its own opening line, almost word for word: *"a table over rules, take
the first that matches, then spend."*

Nothing in it decides anything a rule could have decided. *Done* is the output
of a rule that spends `stop`; *refocusing* is a rule that spends `unattend`;
*suspend this line of work for another* is two more (`push`, `pop`). The loop
knows a score, a match, and that a rule said stop — never what any of them is
for.

## What moving them taught

The shipped bundle used to hold nineteen rules: what an emission means, what a
taken act means, the agent asserting its own acts, denial as a term reconciled
with denial as a sign, four ways an expectation can be disappointed,
means-ends expansion, subgoal checking, giving up, a three-rule call stack.
Every one of them was a policy about how to conduct oneself, and none of them
was a convention of *reading*.

They went with the machinery they were written against. `ugm/rules/bundle.ugm`
says so in its own header, and states the finding plainly: the bundle that
ships today holds **one** rule.

```
len(m.bundle) == 1
[r.name for r in m.bundle] == ["intake"]
```

`<intake>` — *what an arrival means* — survived because it's the one rule that
really is about reading, and the one that could not be written by anyone but
the engine before the bundle existed: `arrived` was unnameable in a corpus.
Everything else — eighteen rules' worth of policy — is now something a corpus
writes for itself, where a claim about how to conduct oneself belongs, rather
than something the engine ships as a default.

Each of the phases that used to be there taught something on its way out, and
the lessons outlasted the code:

**Splitting a phase shrinks it rather than relocating it.** Intake became the
smallest unarguable record of a boundary event — *the channel said this* — and
*what a report means* became a rule. The phase didn't move; it got smaller,
down to the one line `<intake>` still is.

**A phase can hide a claim about what comes first.** Every phase that ran first
was asserting that it *should*, where nothing could argue. As rules they're
merely installed first, so the authored-order tiebreak prefers them — and a
corpus can now say otherwise.

**Being machinery never made it a phase.** Crossing the boundary is
irreducible. Crossing it *on the agent's schedule* was a claim, and a false
one — which is why `Machine._deliver` writes the moment something arrives,
never waiting for a tick.

**A branch can hide how many claims it was making.** The four rules that used
to disambiguate a disappointed expectation are the finding: one comparison,
four claims.

**Data rots in a way a branch does not.** Most of that eighteen-rule policy
layer was unexercised by the time it was measured. A dead branch is dead code;
a rule that never applies costs nothing, breaks nothing, and looks exactly
like a rule that works — which is also most of why it was safe to retire
rather than merely trim.

**The worst offender was control flow, not vocabulary.** The names were always
the easy half; the register work and the nested loop underneath them were the
hard half, and moving them out took the circularity risk with it (Chapter 31).

## The gates

A claim like *zero phases* is only worth as much as the thing that checks it,
and the honest accounting here is that the instrument fleet is shorter than it
used to be — for the same reason the floor and the bundle are shorter than
they used to be.

**What actually runs today:**

```
$ python -m ugm.selftest
...
179 checks, 0 failing
```

```
$ python -m ugm.gates.vocabulary
...
16 checks, 0 failing
```

`ugm.selftest` carries the substrate's own agreement check inline — Chapter
30's `has_var` example, held to `_has_var_slow` over every node a fixture
builds — and a planted-typo control of its own: a rule that reads `typo($x)`,
which nothing writes, has to show up as unwebbed or the check is broken
rather than passing.

`ugm.gates.vocabulary` is the surviving standalone gate. It classifies every
reserved name, checks the classification is total, runs the shipped
passenger-rights corpus for real and asserts its answers, and ends with a
**kill-probe**, in full:

```
a planted typo (watns/wants)   1 unwebbed  ['wants']
```

A rule is loaded that reads `wants` and a fact is written misspelling it
`watns`; the detector has to report `wants` as unwebbed or the run fails. That
line is the "instruments that lied" lesson made concrete and re-run on every
call:

> **An agreement gate that agrees is worth nothing until it could have
> disagreed.**

**What used to run and doesn't any more.** `ugm.gates.agreement`,
`ugm.gates.state`, `ugm.gates.quiescence` and `ugm.gates.bundle` — a floor
gate for the read, one for the maintained state, one for the compiled
quiescence check, and a bundle gate that deleted each shipped rule and
re-ran the suite — existed, and were retired along with most of what they
checked. The state gate is the clean case: it held a second, maintained index
to agreement with a walk over the graph, and `ugm/core/rules.py`'s own
`candidates` explains why holding it stopped being necessary — *"this one
cannot disagree with the graph, because it is the graph."* Once the index
**is** the belief store rather than a copy of it, there is nothing left for a
second implementation to be held to. The bundle gate went the same way its
target did: with nineteen rules down to one, "delete each and re-run the
suite" stopped being an instrument and became a one-line question a reader
can answer by reading `bundle.ugm`.

This is not a quiet loss. A comment survives in `ugm/core/graph.py` still
pointing at `gates/state.py` as if it runs — it doesn't, and that comment is
now wrong. Say so rather than let the book repeat it: an implementation's own
source comments go stale exactly the way a book does, and the fix in both
places is the same, run the thing before you cite it.

!!! note "Deep dive: instruments that lied"
    A partial list, because it's more instructive than any success:

    - A benchmark defining "the wall is scale" was the **worst case** — 99.6% of
      candidates applied on that fixture against 10.6% across the real suite.
    - A census under-counted by **3.5×** because it tracked objects by identity,
      and identities are reused the moment an object is collected.
    - A check was guarded twice over by later *improvements*, so it had quietly
      stopped being able to fail.
    - A kill-probe that swapped in a byte-length-identical file restored to an
      identical size and timestamp, so the runtime reused the probe's cached
      bytecode — and the probe's result looked permanent. It imitated the very
      bug the control existed to catch.
    - A comparison aimed at a moving target went vacuous.
    - A deterministic computation ending in an unordered collection had a
      tie-break nobody authored.
    - A homogeneous fixture was used to measure a discriminator, and could not.

    And twice, prose claimed more than the probe supported — including once in
    this project's own notes, written up as a win before the measurement came in.

## The judgement census

The other question worth asking of an implementation:

> **Which judgements does the machinery make that no rule can argue with — and
> if one were wrong, how would anyone find out?**

That's not a purity exercise. It has a precise definition:

> **A seam is where the agent stops being able to be wrong about something.**

If it's a rule, it can be wrong, and being wrong leaves a trail. If it's a
branch, it can only be *different*, and difference is invisible.

The census found a small number, and two of them were repaired the same way: the
strength of a claim became a wrapping term (`+likely(p)` rather than a grade
beside `p`), and the precedence table became a claim read from the graph —
which was the step before precedence went entirely.

One general finding came out of it that's worth keeping:

> **A judgement with two defensible answers is sometimes a question asked at the
> wrong level.**

## Two piles, where there used to be three

Applied honestly, an audit of this implementation's host-language code puts it in
two piles now rather than three.

| what | why it's in Python | verdict |
|---|---|---|
| matching, arbitration, belief lookup | irreducible, or the belief store IS the state rather than an index over it | **floor** — nothing stands over it to hold it to, because there is no second definition left to disagree with |
| the doors — pushing/popping a frame, answering a tool request, registering a computator | **doors, not questions** | argued: each needs something anchored a generic rule cannot name |
| ~~a precedence table~~ | ~~a cache of `overrides` facts~~ | **debt, and deleted** |
| ~~the maintained state index~~ | ~~an optimisation of a semantics~~ | **collapsed into the thing it indexed, so there is nothing left to gate** |

The test that used to separate these piles still holds where there's still
something on both sides of it:

An **optimisation** has a slow definition it can be held to, and a gate doing
the holding — so a divergence is a *bug*, findable and reported. `has_var`
against `_has_var_slow` is the one still standing in this shape.

A **cache of a claim** has no slow definition, because the claim *is* the
definition. A divergence is *silence*, and the two ways it can be wrong are
both invisible.

> **An optimisation of a semantics is licensed by a gate that holds it to a
> slow definition. A cache of a claim is debt. And an index that collapses
> into the state it indexes needs neither — there's nothing left to disagree.**

Which is exactly why deleting the precedence table cost nothing, deleting the
state gate cost nothing once the state it guarded stopped existing separately,
and the one gate still worth running — `ugm.gates.vocabulary` — is the one
checking something that has no slow-path twin at all: *what a corpus can name*
is a fact about the source text, not an optimisation of anything, and the only
way to know it's right is to run it.

---

**Next:** the last part. If meaning is what follows from a word, what happens
when nothing follows?
[Meaning is a web →](../horizon/33-the-web.md)

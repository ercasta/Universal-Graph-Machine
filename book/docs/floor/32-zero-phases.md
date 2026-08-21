# Zero phases

Chapter 30 stated a test with a falsifiable consequence:

> **The interpreter's step should have no phases.**

Match, commit, write — and intake, supposition, acting, deviation and goal
expansion become rules that those apply. The count of phases is a direct measure
of how much of the taught layer has escaped onto the floor, and it's a number an
implementation can print.

It prints **zero**.

The step is: score → take the first rule in the window whose antecedent
matches → apply it → spend its postconditions. Plus widening when the window
runs dry, and ending when a rule spent `stop`.

Nothing in it decides anything a rule could have decided. *Done* is the output
of a rule that spends `stop`; *refocusing* is a rule that spends `unattend`;
*suspend this line of work for another* is two more (`push`, `pop`). The loop
knows a score, a match, and that a rule said stop — never what any of them is
for. (An earlier version of this design ran a longer step — recall, match,
defeat, quiescence, arbitrate, apply — and the phase count was zero there too;
Chapter 28 is the story of how the longer step lost to this one on
measurement.)

## What moving them taught

Each of the phases that used to be there taught something on its way out, and
the lessons are more transferable than the count.

**Splitting a phase shrinks it rather than relocating it.** Intake became the
smallest unarguable record of a boundary event — *the channel said this* — and
*what a report means* became a rule. The phase didn't move; it got smaller.

**A phase can hide a precedence claim.** Every phase that ran first was asserting
that it *should*, where nothing could argue. As rules they're merely installed
first, so the authored-order tiebreak prefers them — and a corpus can now say
otherwise.

Two thirds of this agent's arbitrations are still settled by that order, which is
why the shipped rule file is worth reading as an argument rather than as a list.

**Being machinery never made it a phase.** Crossing the boundary is irreducible.
Crossing it *on the agent's schedule* was a claim, and a false one.

**A branch can hide how many claims it was making.** One deviation comparison
became four rules, and the count is the finding.

**Data rots in a way a branch does not.** Three of those four rules were
unexercised. A dead branch is dead code; a rule that never applies costs
nothing, breaks nothing, and looks exactly like a rule that works.

**The worst offender was control flow, not vocabulary.** Supposition's phase was
three lines of register work and a nested run of the loop. The names were the
easy half.

## The gates

A claim like *zero phases* is only worth as much as the thing that checks it. So
this design runs a set of gates, and the interesting thing is what each one had
to be built to survive.

**The floor gate.** For every taught convention, the rule-level definition
exists, and the compiled path is held to it — on **every look, in every
fixture**, not on a test case. Three of these run: one for the read, one for the
state, one for the move. Each caught something no fixture could.

> **An optimisation of a read is a re-implementation of its semantics**, so the
> slow definition stays and the fast path is held to it against a moving target.

**The bundle gate.** Delete each shipped rule, one at a time, and re-run the
suite. Report any rule whose removal breaks nothing.

**The kill-probe rule.** Every gate must be shown to be *capable* of
disagreeing:

> **An agreement gate that agrees is worth nothing until it could have
> disagreed.**

This is not paranoia. It is the single most common way an instrument in this
project has lied.

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
strength of a claim became a wrapping term, and the precedence table became a
claim read from the graph.

One general finding came out of it that's worth keeping:

> **A judgement with two defensible answers is sometimes a question asked at the
> wrong level.**

## Three piles, and only one is debt

Applied honestly, an audit of this implementation's host-language code puts it in
three piles:

| what | why it's in Python | verdict |
|---|---|---|
| the maintained state, the argument index, the walk order | optimisations of a semantics | **licensed** — three floor gates hold them to the slow definition every tick |
| the doors — entering a supposition, dispatching an intent, adopting a rule | **doors, not questions** | argued: each needs something anchored a generic rule cannot name |
| answerer bodies | what a tool *is* — a request answered by a function | right by the design's own rule |
| ~~a precedence table~~ | ~~a cache of `overrides` facts~~ | **debt, and deleted** |

The test is what happens when the fast path and the definition disagree.

An **optimisation** has a slow definition it can be held to, and a gate doing the
holding — so a divergence is a *bug*, findable and reported.

A **cache of a claim** has no slow definition, because the claim *is* the
definition. A divergence is *silence*, and the two ways it can be wrong are both
invisible.

> **An optimisation of a semantics is licensed by the floor gate. A cache of a
> claim is debt.**

Which is exactly why deleting the precedence table cost nothing and deleting the
state index would cost an order of magnitude.

---

**Next:** the last part. If meaning is what follows from a word, what happens
when nothing follows?
[Meaning is a web →](../horizon/33-the-web.md)

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

## The bundle

Conventions the engine ships as data rather than as loop phases live in
`ugm/rules/bundle.ugm`, and the whole bundle is one rule:

```
len(m.bundle) == 1
[r.name for r in m.bundle] == ["intake"]
```

`<intake>` — *what an arrival means* — is the one rule the engine has to ship
rather than a corpus author: `arrived($channel, $said)` names a boundary
crossing, and a channel is anchored while a rule is generic, so deciding that
an arrival is a saying has to happen on the machinery side of the line. What
to *do* about a saying is not: everything past "record that this was said"
belongs to a corpus.

## The gates

A claim like *zero phases* is only worth as much as the thing that checks it.

**What runs today:**

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

`ugm.gates.vocabulary` classifies every reserved name, checks the
classification is total, runs the shipped passenger-rights corpus for real
and asserts its answers, and ends with a **kill-probe**, in full:

```
a planted typo (watns/wants)   1 unwebbed  ['wants']
```

A rule is loaded that reads `wants` and a fact is written misspelling it
`watns`; the detector has to report `wants` as unwebbed or the run fails. That
line is a general standard made concrete and re-run on every call:

> **An agreement gate that agrees is worth nothing until it could have
> disagreed.**

## The judgement census

The other question worth asking of an implementation:

> **Which judgements does the machinery make that no rule can argue with — and
> if one were wrong, how would anyone find out?**

That's not a purity exercise. It has a precise definition:

> **A seam is where the agent stops being able to be wrong about something.**

If it's a rule, it can be wrong, and being wrong leaves a trail. If it's a
branch, it can only be *different*, and difference is invisible.

One general finding is worth keeping:

> **A judgement with two defensible answers is sometimes a question asked at the
> wrong level.**

## Two piles

Applied honestly, an audit of this implementation's host-language code puts it
in two piles.

| what | why it's in Python | verdict |
|---|---|---|
| matching, arbitration, belief lookup | irreducible, or the belief store IS the state rather than an index over it | **floor** — nothing stands over it to hold it to, because there is no second definition left to disagree with |
| the doors — pushing/popping a frame, answering a tool request, registering a computator | **doors, not questions** | argued: each needs something anchored a generic rule cannot name |

An **optimisation** has a slow definition it can be held to, and a gate doing
the holding — so a divergence is a *bug*, findable and reported. `has_var`
against `_has_var_slow` is the one still standing in this shape.

A **cache of a claim** has no slow definition, because the claim *is* the
definition. A divergence is *silence*, and the two ways it can be wrong are
both invisible.

> **An optimisation of a semantics is licensed by a gate that holds it to a
> slow definition. A cache of a claim is debt. And an index that collapses
> into the state it indexes needs neither — there's nothing left to disagree.**

The one gate still running — `ugm.gates.vocabulary` — is the one checking
something with no slow-path twin at all: *what a corpus can name* is a fact
about the source text, not an optimisation of anything, and the only way to
know it's right is to run it.

---

**Next:** the last part. If meaning is what follows from a word, what happens
when nothing follows?
[Meaning is a web →](../horizon/33-the-web.md)

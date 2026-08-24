# The read

There is one graph, and it does not contain a summary of itself.

> **The state is what an anchor's presence answers.**

So *does `on(a, b)` hold?* means exactly one thing: is `believed(on(a, b))` in
the graph right now.

This chapter is the single most important program in the machine — the one
every rule runs, every tick, on every member of every antecedent. Everything
in Part 1 up to here exists so this can be cheap and unambiguous, and
everything after Part 1 is written against its answer.

## The whole of it

> **Presence is the answer. There is no second question.**

```
holds(p) = anchor(p) is not None
```

One dictionary lookup, because the anchor is interned: a proposition has at
most one anchor, ever, so there is exactly one place to look and at most one
thing to find. It's worth dwelling on how much this is *not* doing:

- It does not walk anything.
- It does not compare two claims to see which is newer.
- It does not ask *at which moment* — there is no moment to ask about
  (Chapter 4).
- It does not check a stored sign — there isn't one; asserting mints the
  anchor, erasing deletes it, and reading just asks whether it's there.

A claim about a proposition is never *superseded*, because there is never a
second one to supersede it with. Assert `p` while it's already believed, and
you get the same anchor back, unchanged. Erase it, and it's gone. There is no
in-between state where two claims about `p` coexist for the read to choose
between.

!!! note "This used to be a walk, and it was the design's biggest cost"
    An entry used to carry a **locus** — what it was *about* — beside its
    deposit time, so the read had to use both keys in a fixed order: latest
    locus, then latest deposit, with *at-or-before* decided by ancestry rather
    than a depth comparison, because supposing forked the chain. Measured
    before anything was optimised, resolving reads that way was **86% of
    runtime**, and sixteen of every seventeen walks were the same walk
    repeated.

    Three rounds of work, each measured before the next, brought that walk
    down: asking it once per tick rather than once per rule, indexing the
    resolved state by sign and relation, indexing the resolution by
    proposition — together, **67×**. A later pass, maintaining the state and
    everything derived from it in one place instead of rebuilding it, took a
    1,600-fact fixture from 4.79s to 0.48s, and made 12,800 facts run in less
    time than 1,600 used to take.

    None of that machinery exists any more, and none of it needed to survive:
    the locus went (Chapter 4), and with it the two-key walk those three
    rounds were built to speed up. What's left isn't a fourth optimisation of
    the same walk — it's a walk with nothing left to walk. The read didn't get
    faster again. It got structurally simple, which is a different kind of
    win, and the numbers above are history, not a benchmark of what runs
    today.

## A read that never changes is still asked

Reading costs nothing, but *asking* happens on a schedule you don't control —
every tick, for every rule whose shortlist might contain it. That has a
consequence Chapter 0 already ran into and is worth stating precisely here:

> **The engine does not decide, on your behalf, that a match is no longer
> worth acting on.**

A rule whose antecedent is still satisfied is still offered a chance to apply,
whether or not applying it would write anything new:

```
rule <flip> = implies( { +on(light) }, { -on(light), +off(light) } )

fact +on(light)
```

```
$ python -m ugm flip.ugm --ask "on(light)" --ask "off(light)"
flip.ugm: 2 ticks, ended quiescent

on(light): not believed

off(light): believed
```

This one quiesces cleanly, in two ticks, because the *consequent itself*
removes the thing the antecedent needed — erasing `on(light)` is what stops
the rule from matching again. That's the general pattern: a rule stops itself
by spending what it matched, or by asking for the absence of what it's about
to conclude (`no mortal($p)` from Chapter 0). Nothing in the loop counts how
many times a rule has fired, and nothing notices that reapplying it would be
pointless — that judgement belongs to the corpus, every time.

!!! note "Deep dive: a relationship can be more than one thing"
    `holds` asks about one node — right when the node names the *subject*, an
    entity other facts get to be about. Absence isn't that question. `no
    p($x)` asks whether *anything at all* claims `p(x)`, and there's a second
    way to build a proposition, `instance`, that mints a fresh node rather
    than reusing the interned one — for a relationship that is itself an
    entity two people can independently claim. `no` has to check every one of
    those, or a second unbelieved claim sitting beside the first would let
    `no p(x)` answer *nothing says this* while something plainly does.

## The scoring

| | overwrite in place | keep the chain, walk it (gone) | **one anchor, one lookup** |
|---|---|---|---|
| not leaking | a revision and the claim it revises are indistinguishable | each claim survived; the last one, found by a walk, governed | there is only ever one claim to find |
| not lossy | history is gone | nothing was overwritten | history is gone — a stated trade (Chapter 4), not an accident |
| readable | a lookup | a walk with two orderings and two ancestry tests | **a lookup**, and there's nothing behind it to have gotten wrong |
| composable | two writers contend | appending was the only write | asserting is idempotent; two writers land the same anchor |

The middle column cost this project real measured time to build and more to
speed up. The last column didn't need speeding up, because there was nothing
left to be slow. That's the shape of the whole first cut this book has walked
through: not "optimise the mechanism" but "ask whether the mechanism was
buying its keep," and here the honest answer was no.

---

That's Part 1. You now know what memory looks like: nodes with ordered
members; propositions that claim nothing; an anchor that claims them by being
present; and one lookup that answers *is this true* with nothing to walk.

Everything from here is **taught**, not built in.

**Next:** the first and most important thing you teach it.
[A rule is a fact about two moments →](../rules/06-a-rule-is-a-fact.md)

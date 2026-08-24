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

Scored against the same four criteria the rest of this design answers to
(Appendix): a single anchor is **not leaking** — a revision and the claim it
revises can't be confused, because there is only ever one claim to find. It
is **readable** — a lookup, with nothing behind it to have gotten wrong. It is
**composable** — asserting is idempotent, so two writers land the same
anchor. It is **not lossy** only in the narrow sense that nothing is silently
overwritten; a history of *how belief changed* is not kept, and that's a
stated trade (Chapter 34), not an accident.

---

That's Part 1. You now know what memory looks like: nodes with ordered
members; propositions that claim nothing; an anchor that claims them by being
present; and one lookup that answers *is this true* with nothing to walk.

Everything from here is **taught**, not built in.

**Next:** the first and most important thing you teach it.
[A rule is a fact about two sides →](../rules/06-a-rule-is-a-fact.md)

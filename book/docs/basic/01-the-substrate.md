# Nodes, members, and nothing else

Everything in this machine is built out of two things.

- There are **nodes**, and directed **edges** between them.
- A node may have **ordered members**: an edge to a target at a known position.

That's it. In particular:

> Edges carry no labels, no attributes, and no truth values. Anything you want
> to say about a connection has to be a node.

That last line is the whole design in one sentence, and it is worth sitting
with, because most graph systems do the opposite.

## A labelled edge, done properly

Elsewhere you'd draw `a --on--> b` and be done. Here, `on` is not something an
edge can be. So the connection becomes a node of its own:

```
on(a, b)        a node whose members are, in order, a and b
```

This is called a **relation instance**. It has a relation (`on`) and two
members, and the order matters — position 0 is `a`, position 1 is `b`.

Why go to the trouble? Because a node can be pointed at, and an edge cannot.

```
on(a, b)                       the idea that a is on b
said_by(<that node>, anna)     ...and Anna is the one who said it
mistaken(<that node>)          ...and I now think that record was wrong
```

If `on` were an edge label, none of the second two lines could be written
without inventing a new mechanism for talking about edges. Because it's a node,
they're just more relation instances. Nothing was added.

## Everything is this shape

This is why the rest of the book can keep saying "and that's an ordinary fact
about it". Rules, claims, moments, stretches of time, plans, prohibitions, the
machine's own goals — all of them are nodes, so all of them can be spoken about
without introducing a new kind of thing.

```
person(paul)                       a proposition about a person
rule(<mortality>)                  a fact about a rule
by(<mortality>, boss)              who authored that rule
dormant(<undead>)                  a rule that is out of the running
```

Four lines, one shape, four completely different subjects.

## Why ordering is provided

You could get rid of ordered members. You'd encode each position as its own
little node — *this slot holds position 1, and its filler is `a`* — which is
roughly what RDF does. One node and three edges become three nodes and seven,
and it works.

It is not done here, and the reason is precise:

> With ordered members, matching a pattern against a thing is **linear in the
> pattern**. With unordered edges, matching becomes subgraph isomorphism.

Ordering *fixes the correspondence* between the parts of a pattern and the parts
of the thing you're matching it against. Take it away and the machine has to
search over which edge answers to which — the same problem, and hard in general.
Since matching happens on absolutely every step, that cost would be paid
forever.

So ordering is here **by economy**, not by necessity, and Chapter 30 says so out
loud. It's one of only two things on the floor that could in principle be given
up.

## One index, and one rule about indexes

The substrate keeps exactly one lookup table: **instances, by relation**. If a
rule mentions `on`, it has to start its search somewhere, and the alternative is
scanning every node in memory.

One condition governs every index in this design:

> **Index what was asserted. Never index what was derived.**

An index over asserted structure is just storage — it summarises writes, and a
write is permanent. An index over *derived* values is a cache of something that
might stop being true, and keeping such a cache correct means propagating
invalidations across a web of dependencies: a second machine, with its own
consistency problem, running underneath the first.

That rule gets invoked several times later in the book, always to delete
something. It's the reason there is no stored "how sure am I" number
(Chapter 15) and no stored table of which rule beats which — and in the end no
relation for it either (Chapter 17).

!!! note "Deep dive: filing the same thing twice is still storage"
    Filing an entry by relation alone makes some searches quadratic — a rule
    asking about `child(?p, ?x), child(?x, ?y)` would draw every `child` fact
    for each binding of the first member. Filing each entry *additionally* under
    each of its arguments, and walking whichever member narrows first, turned
    2,006,004 comparisons over 1,000 facts into **3,003** on the measurement
    that prompted it.

    Both filings are over what was asserted, so neither is a cache. That's the
    difference between an optimisation and a debt, and Chapter 32 makes it a
    rule.

## Two things have no bucket

Two kinds of pattern can't be filed, and it's worth knowing which:

- a **bare variable** — `?p`, matching anything at all;
- a pattern whose **relation** is a variable — `?kind(?item)`.

Neither says anything about what it names until it matches, so both fall back to
scanning. That is the price of the two most general things the language can say.
Measured on a small world with 200 unrelated facts, an antecedent member with a
variable relation cost **14× the comparisons** of the equivalent concrete rules.

They are both allowed. Chapter 8 shows what the second one buys — it's how *the
smith sells weapons* becomes a fact rather than a rule per merchant — and where
to put it so the cost doesn't bite.

---

**Next:** we have somewhere to put things. Now: what does it look like to
actually *claim* something?
[A proposition claims nothing →](02-propositions-and-entries.md)

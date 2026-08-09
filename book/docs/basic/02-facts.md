# Telling it things

We've seen the world is made of dots and named arrows. Now let's put something
into it — and then meet the machine's idea of *what counts as a proper shelf*.

That second half is the interesting one, and it works in a way that surprises
most people.

## Building a bit of world

There are only two moves. **Mint** a node, and **link** it to another:

```
shelf  = mint a "shelf"
salt   = mint a "jar", labelled salt
link shelf ──jar──> salt
```

That's the whole vocabulary for building. Everything you'll ever tell the
machine is some number of mints and links, plus attributes set on nodes.

One rule of housekeeping matters more than it looks: **real things hang off the
root**. There's a node called `root`, and anything genuinely part of the world
is reachable from it. This isn't bureaucracy — in Chapter 6 the machine starts
making private copies of the world to think in, and "reachable from root" is
exactly what separates the real shelf from an imagined one. Without it, the
machine would eventually offer you a plan about a shelf it only daydreamed.

## What makes something a shelf?

Here's where it gets interesting. We can describe what a shelf *is*:

```
a shelf has 3 jars
```

That's a **type**. And now the important question: how does the machine decide
whether some node is a shelf?

It doesn't look for a tag. It **looks at the node**.

We have a shelf with two jars on it. Ask:

```
is it a shelf?     : False
what's wrong       : {'jar': ('3 of kind jar', '2')}
```

Not a shelf — and it tells you precisely why: it wanted 3 jars of kind `jar`,
and found 2. Now put a third jar on:

```
after a third jar  : True
```

Nothing was declared. Nothing was tagged or re-registered. The node became a
shelf **because its structure changed**, and the answer is recomputed the moment
you ask.

!!! note "A type is a shape, not a badge"
    This is the opposite of how most systems work. Usually a thing "is a Shelf"
    because someone stamped it Shelf, and the stamp can drift out of line with
    reality — you can remove every jar and the stamp still says shelf. Here
    there's nothing to drift, because there's no stamp. A node satisfies the
    shape or it doesn't, checkable now, every time.

## Working out what something is

Because types are shapes, you can also ask the open question — *what is this?*

```
what is it, then?  : ('shelf',)
```

Nothing was searched for. The machine checked the shapes it knows against the
node in front of it. And two consequences fall straight out, without any
machinery to support them:

- **A thing can be several types at once.** A washed car is also a serviced car,
  if it satisfies both shapes. No conflict to resolve.
- **A thing can stop being a type.** Take a jar off, and it's no longer a shelf.
  Nothing needs invalidating, because nothing was ever stored.

Those two behaviours usually cost real effort to build. Getting them for free is
a sign the shape of the idea is right.

## Why this matters later

Hold on to this, because Chapter 4 leans on it entirely:

> **If a type is a shape, then changing a thing's type is just changing its
> shape.**

Sealing a jar doesn't *record* that a sealing happened. It puts the lid on — and
afterwards the jar satisfies the shape "sealed jar". There's no separate notion
of an action's *effect* to keep in sync with what the action does, because the
effect is just the shape the thing ends up satisfying.

That one move deletes a surprising amount of machinery. We'll see it work in two
chapters.

!!! note "Deep dive: the honest limit"
    A shape describes each arrow-name independently: *3 jars*, *1 lid*. It can't
    say "the jar on the left must be taller than the jar on the right", because
    that's a relationship *between* two parts. Nor can it reach two levels deep
    — "a crate on a crate that's on the ground" isn't expressible as a shape,
    which is exactly why the tower in Chapter 0 was described as two separate
    `on` facts rather than as a type. Real limit, stated rather than hidden.

---

**Next:** now that the machine holds a world, let's ask it something — and meet
the three answers it can give. [Asking →](03-questions.md)

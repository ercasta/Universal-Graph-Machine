# The substrate

In the last chapter we watched the machine build a tower. Before we go further,
let's look at the world it does its thinking *in*. It turns out to be
astonishingly simple — just **dots and named arrows**.

The technical name for this world is the **substrate**: the raw stuff everything
else is built from. Think of it like LEGO. There's really one kind of brick, and
yet you can build anything — including, eventually, the machine's own rules,
goals and memories. All of it lives here.

We'll use a kitchen for the rest of Part 1.

## One kind of thing: a node

Every *thing* the machine knows about is a **node** — picture a dot.

```
 (kitchen)     (shelf)     (salt)     (pepper)     (oil)
```

Notice something already: a room, a piece of furniture, and three jars are all
just dots. The machine has no separate boxes for "places" and "objects". One
kind of thing, all the way down.

A node carries a **kind** and any number of **attributes** — plain facts about
it that aren't relationships to anything else:

```
kind of shelf      : shelf
attributes         : {'kind': 'shelf', 'label': 'shelf', 'height': 3}
```

`height: 3` is an attribute. So is `label: 'shelf'` — and that word *label*
deserves a warning we'll come back to hard in Chapter 9:

!!! warning "A label is a convenience, not an identity"
    The machine does not identify things by name. `label` is a human comfort,
    like a sticky note. Two jars can carry the same sticky note. When you say
    "the salt", the machine has to *look it up* — and if two things answer to
    that name, the honest response is to refuse, not to guess. Nothing here is
    identified by name alone.

## Arrows have names

Two nodes are joined by an **edge**, and every edge carries a name:

```
   (kitchen) ──contains──> (shelf) ──jar──> (salt)
                                   ──jar──> (pepper)
                                   ──jar──> (oil)
```

Read them out loud: *the kitchen **contains** the shelf; the shelf has a **jar**,
salt.* The arrow's name is the relationship.

You can ask a node which arrows lead out of it:

```
labels out of shelf : ('jar',)
```

The shelf has jars and nothing else.

## Arrows are in order

Here's something small that turns out to matter a great deal. When several
arrows share a name, they're kept **in order**:

```
jars, in order     : ['salt', 'pepper', 'oil']
the 2nd jar        : pepper
```

So a one-to-many relationship is also a *list*, for free, and "the second one"
is a real question you can ask. That sounds like a detail. It isn't — when we
get to Chapter 14 and the machine turns a sequence of things it did into a
reusable procedure, the order of those steps is native to the substrate rather
than something bolted on with a counter.

## Arrows run backwards too

Ask any node what points *at* it:

```
what contains it   : ['kitchen']
```

The machine keeps this index maintained as you build, so looking backwards is as
cheap as looking forwards. That's what makes "what was this jar used for?" and
"which plans touch this crate?" answerable at all.

## What is *not* here

Three absences are deliberate, and each one saves a whole category of trouble.

**No separate place for rules.** A rule is stored in this same graph, as nodes
and edges. So is a goal, so is a plan, so are the machine's notes. There is one
world, and everything is in it. Chapter 4 is where that stops being a slogan.

**Nothing fires by itself.** Putting a fact in the graph does not wake anything
up. In a lot of reasoning systems, adding a fact triggers every rule that
matches it, and the hard part becomes stopping things from happening. Here
nothing happens until something is *pointed* at something. Chapter 4, again.

**No hidden history.** The graph holds what is true *now*. If you want a record
that something changed, that record is an ordinary node you can point at — not a
private log the machine keeps for itself.

!!! note "Deep dive: references aren't edges"
    An edge is a claim: *the shelf has this jar*. But sometimes you want a node
    to merely **hold a pointer** to another — a bookmark, not an assertion. The
    machine keeps those distinct: a *reference* is stored as an attribute value,
    and it doesn't add anything to what the graph asserts. Confusing the two
    would mean every bookmark quietly became a claim about the world.

## Where we are

The whole substrate is: **nodes with attributes, joined by named ordered edges,
navigable both ways.** That's it. Everything in the rest of this book is built
out of exactly this.

---

**Next:** how you put something *into* this world — and how the machine decides
whether what you built is a proper shelf. [Telling it things →](02-facts.md)

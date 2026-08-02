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

## An arrow is a thing too

Nodes aren't the only things you can point at. Every edge has its own
**identity** — a name of its own — and that identity survives having other
arrows inserted around it:

```
jars, in order  : ['salt', 'pepper', 'oil']
                  ↑        ↑         ↑
                  e1       e3        e2      ← the arrows' own names
```

`pepper` was slipped into the middle *after* the other two. Its position is
second; its identity is whatever it always was. Positions shift; identities
don't.

An edge can also carry **properties** of its own — small notes about the
connection rather than about either end. *The shelf has this jar* is the edge;
*and it was put there second* is a property of that edge.

Why this matters: because an edge is a thing, other things can point at it. In
[Chapter 29](../world/29-when-things-happened.md) a moment in time points at
an arrow to say *this connection appeared then* — which is how the machine can
answer "when did this jar arrive on this shelf?" rather than only "what's on the
shelf now?"

!!! note "The alternative that was tried and dropped"
    An earlier version of the machine had nameless arrows, and turned every
    *role* into a node so that connections could be pointed at. That worked and
    charged a node plus two extra arrows for **every** connection in the graph,
    to buy something needed in a small minority of cases. Named arrows that can
    optionally be pointed at cost nothing in the common case.

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

# The substrate

In the last chapter we watched the machine solve a crime. Before we go further,
let's look at the world it does its thinking *in*. It turns out to be
astonishingly simple — just **dots and arrows**.

The technical name for this world is the **substrate**: the raw stuff
everything else is built from. Think of it like LEGO. There's really only one
kind of brick, and yet you can build anything.

## One kind of thing: a node

Every *thing* the machine knows about is a **node** — picture a dot with a name.

```
 (ada)      (bo)      (library)      (suspect)
```

Notice something already: `ada`, `library`, and `suspect` are all just dots.
The machine doesn't have separate boxes for "people" and "places" and
"categories." A thing is a thing. What *kind* of thing it is comes from how it's
connected — which is the next idea.

## Facts are arrows

A **fact** connects things with an arrow that points from one to another. Our
fact `bo in library` looks like this:

```
 (bo) ──in──▶ (library)
```

The arrow has a **direction** — it goes *from* bo *to* the library — and that
direction matters. `bo in library` and `library in bo` are very different
claims! The direction is how the machine keeps *who did what to whom* straight.

Here's the whole opening of our detective case, drawn out:

```
      (ada) ──is_a──▶ (suspect)
      (bo)  ──is_a──▶ (suspect)
      (cy)  ──is_a──▶ (suspect)

      (bo)  ──in────▶ (library)
      (ada) ──is────▶ (alibied)
```

That's it. That's the entire "world" from Chapter 0 — five arrows between eight
dots. Everything the machine deduced, it deduced from this little picture.

!!! note "Facts you state vs. facts it works out"
    The arrows above are the ones *we told it*. When the machine reasons, it
    adds **new** arrows — `(cy) ──is──▶ (thief)` appeared because a rule fired.
    New knowledge is just new arrows in the same picture. There is nowhere else
    for knowledge to live.

## Attributes: notes stuck on a dot

Sometimes a thing has a quality that isn't really a *relationship* to another
thing — it's just... a property of the thing itself. A node can carry little
notes called **attributes**, like a sticky note on the dot:

```
 (ada)
   name = "ada"
```

You'll mostly meet attributes later, when we get to shades of grey — like a clue
that's *probably* true rather than definitely true. For now, just know the dots
can carry notes.

## Why so bare?

You might wonder: why build a reasoning machine out of such plain parts? Most
systems have rich, specialized structures — tables, objects, categories baked
into the foundation.

The Universal Graph Machine bets the opposite way. Keep the foundation *dumb* —
just dots and arrows — and put all the cleverness in the **rules** that reason
over it. Because the world is so plain and uniform, the machine can treat every
problem the same way. A fact about a suspect and a fact about a chemical and a
fact about a chess move are all *just arrows*, so the same reasoning machinery
works on all of them. That's the "Universal" in the name.

??? info "Deep dive: this is a *graph* (and why there are no labels on the wires)"
    A collection of dots joined by arrows is, in mathematics, called a
    **graph** — the dots are *nodes* (or *vertices*) and the arrows are *edges*.
    It's the same idea behind a map of subway stations, a friend network, or a
    family tree. If the word "graph" is new, the [appendix has a gentle
    introduction](../appendix/index.md#what-is-a-graph).

    There's a subtle design choice hiding here. You might expect the *arrow
    itself* to be labelled "in" or "is_a". Instead, the machine treats the
    relationship as part of the connected structure — the **shape** of how the
    dots link up carries the meaning, not a label painted on the wire. This
    "label-less" discipline is a deliberate and slightly unusual choice; it's
    what lets the machine stay so uniform. You don't need it to use the machine,
    but it's one of the ideas that makes it tick, and we'll return to it in the
    advanced part.

## Try it

Open the playground and add a brand-new dot to the world. Type a new line —
`dz is a suspect` — then ask `who is thief` again. A fresh suspect with no alibi
and no library sighting has nothing clearing them, so watch **dz** join the list
of thieves. You just added a dot and an arrow, and the machine's answer changed.

[:material-play-circle: **Open the playground**](../playground/detective.md){ .md-button }

---

**Coming next (Part 1 continues):** now that we know what the world is made of,
we'll get systematic about the three things you can *do* with it — state facts,
ask questions, and write rules.

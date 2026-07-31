# Types as shapes, and change as a cast

Chapter 2 told you a type is a shape rather than a badge. This chapter is about
how much that one decision removes.

## A shape, written out

```
a car has 4 wheels
a serviced car is a car, and is serviced
```

Two shapes. The first constrains structure — an arrow named `wheel`, four of
them, each pointing at a wheel. The second adds an attribute requirement.

Now a car with four wheels:

```
is a car?           True
is a serviced_car?  False
```

Service it — which is to say, set `serviced`:

```
after servicing     True
```

Nothing was re-registered. The node satisfies a stronger shape than it did a
moment ago, and the answer changed because the question is re-asked every time.

## Change doesn't need representing

Here's the consequence, and it's a big one.

`service(c: car) -> serviced_car` promises to turn a car into a serviced car.
In most designs that promise needs machinery: a precondition, a description of
the effect, and something ensuring they stay in step with the code.

Here it's a **cast**. The rule takes something satisfying one shape and leaves
it satisfying a stronger one. Whatever it changes along the way is merely *how*
the cast is achieved.

And crucially: **nothing records that a change happened.** There's no event, no
version, no history entry. A node either satisfies the shape now or it doesn't —
which is checkable at this moment, rather than being a claim about the past that
could be wrong.

So a rule's precondition is just its **parameter shape**, and its effect is just
its **result shape**. Both are already in the signature. Two whole concepts
collapse into the type declaration, and the planner in Chapter 7 chains casts
without any separate notion of an operator's effects.

!!! note "Why 'a cast returns its subject'"
    When a rule doesn't explicitly produce something new, the thing it returns
    is the thing it was handed. That isn't papering over an ambiguity — it's the
    common case. Sealing a jar gives you *that jar*, now sealed. Creating
    something genuinely new is the case that has to say so.

## Sub-shapes are structural too

```
serviced_car is a kind of car? True
```

Nobody declared that relationship. A serviced car requires everything a car
requires plus more, so it *is* a kind of car — worked out by comparing
constraints, not by consulting a hierarchy.

Two consequences fall out for free:

- an argument wanting a `car` accepts a `serviced_car`, because the check is
  about constraints rather than names;
- a rule producing a `serviced_car` can satisfy a goal wanting a `car`.

You can write two shapes independently, never mention one in the other, and they
still stand in the right relationship if their constraints say so.

## Asking the open question

Everything above asks about a *named* shape. The interesting direction is the
other one — *what is this?*

```
what is it?         ('car', 'serviced_car')
```

Both, at once, with no conflict to resolve, because they're independent
structural facts. And go the other way:

```
remove a wheel ->   ()
```

It's no longer a car. Nothing had to be invalidated, no cache updated, no event
fired — because nothing was ever stored.

That's the tell that the shape of the idea is right: multi-membership and
de-recognition usually cost real machinery, and here they're consequences.

!!! warning "The one that bit"
    The machine does keep a *hint* — a note saying "this was recognised as a car
    once", to avoid re-searching every shape it knows. An early version read
    that hint as authoritative, and it drifted: remove a wheel and the note
    still said car, so a learned rule took its parameter type from a shape the
    node no longer satisfied — producing a rule that would refuse its own
    training example. The rule now is: **cache the candidate, re-validate on
    read.** Checking one named shape is cheap; searching all of them isn't. Drift
    became structurally impossible rather than merely unlikely.

## The honest limits

Two, both real, both stated rather than worked around.

**A shape is one level deep.** It checks that an arrow points at something of a
kind — it doesn't recurse into *that* thing's shape. So "a crate on a crate
that's on the ground" isn't expressible, which is why Chapter 0's tower was two
separate `on` facts.

**A shape constrains one argument at one call site.** It can't say `b ≠ onto`
for `stack(b, onto)`, because it describes each thing independently and never a
relationship between two of them. The planner enforces that particular one
itself.

Both are the same underlying limit: a shape describes *a* thing, and some truths
are about *pairs* of things. That's what Chapter 5's goal constraints are for —
and it's why goals and types stayed separate rather than one swallowing the
other.

---

**Next:** if a shape can't say what a rule does, what can?
[Reading a rule →](18-reading-a-rule.md)

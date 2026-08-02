# When things happened

Part 6 was the machine looking inward. This part is the machine looking out —
at a clock, at other people, at rules it didn't set, at things it has to wait
for.

We start with time, because until recently the machine had none. Not a poor
notion of time: **none**. There was no clock anywhere in the engine — no reading
of the actual time of day, at all. Four different things stood in for it, and
because none of them was a thing in the graph, none could be compared to any
other.

## The direction is the design

The obvious way to put time in is to stamp things: give each fact a *when*.

The machine does the opposite. **A moment is a node, and it points at what it
dates.**

```
                        ┌──▶ the pan is not hot
   (moment t=…) ────────┼──▶ the pan is clean
                        ├──▶ the pan is on the shelf
                        └──▶ the pan is a pan
```

That arrow direction isn't a convention. Three things follow from it that don't
follow from the other one.

**One look dates many facts.** Glance at the pan and you learn four things about
it at once. That's naturally *one* moment pointing at four things. Stamping
would copy the same reading onto each of them, four times, and then they can
disagree.

**Dating doesn't disturb anything.** Nothing already in the graph is touched to
acquire a time. Which means something can be dated *afterwards*, by something
that doesn't own it.

**It matches the rule the rest of the machine already keeps.** Notes point at
the world; the world never points back at the notes. Chapter 13 made that the
reason the thread doesn't hang off the world. Time is the same shape.

Here's a real look:

```
slots seen in one look    : 4
moments involved          : 1
the moment                : t=1785702199.403 (4 things dated)
the observation's own time : None
```

Four sightings. One moment. And the sightings carry no time of their own —
they'd have to, under the other design.

## Some moments have no time on them

*"A minute after the pan is hot."*

That's a perfectly ordinary thing to say, and there is no clock reading in it.
There can't be — the pan isn't hot yet. So a moment is allowed to carry no
stamp at all and be placed purely by what it comes after:

```
"a minute later" has a stamp?  None
is "pan is hot" before it?     True
is it before "pan is hot"?     False
```

Ordering is therefore **partial**, not a line. Some pairs of moments simply have
no order between them, and the machine says so by answering *no* in both
directions:

```
is the look before "pan is hot"?  False
is "pan is hot" before the look?  False
```

Two falses means *unordered*, which is not the same as *after*. Ask both ways to
tell them apart. This is the same honesty Chapter 28 showed for *where*: when
two things aren't comparable, inventing an order between them is worse than
admitting it.

And when you ask for a timeline, the undated moments are **dropped**, not
shuffled to one end:

```
timeline of (pan is hot, a minute later, the look) : 1 moment long
```

Putting a relative moment at either end of a line would be an invention. It has
no position on that line.

!!! warning "A timer on a relative moment refuses"
    Ask *"has 'a minute after the pan is hot' arrived yet?"* and the machine
    raises rather than answers:

    ```
    ... is a relative moment with no absolute stamp, so nothing can say
    whether it has arrived. Place it with `before`, or give it an `at=`.
    ```

    Both alternatives are worse. Answering *no* makes a timer that silently
    never fires — indistinguishable from one that's merely early. Answering
    *yes* fires it immediately. Chapter 32 is built on this refusal.

## One action, one moment — including what it produced

Here's the rule that took a second pass to get right.

List a folder. The action does two things: it *sees* facts about the folder, and
it *creates* nodes for the files it found. The first version dated the sightings
and left the file nodes with no time at all.

Which is to say: listing a folder left **the file list — the entire point of
listing a folder** — undated.

```
files produced           : 3
moments over the look    : 1
moments over the products: 1
same moment?             : True
```

One action is one moment, and that covers what the action *produced*. If the
files each got their own moment, that would be four actions, not one — exactly
the per-thing stamping this design rejects.

!!! note "Dating is not noticing"
    The products are dated. They are **not** recorded as things that were seen:

    ```
    sightings on a produced file : ()
    ```

    Those are different questions and they have opposite defaults, which
    Chapter 24 made a point of. What the machine *encodes* is deliberately
    narrow — only the slots of the thing it was actually looking at, because
    everything else the tool happened to touch is the walk to school. What the
    machine *dates* is broader: something the world just handed you, with no
    time on it, can't be aged or compared or told apart from something that was
    always there.

The obvious generalisation — date everything the moment it's created — is wrong,
and it's worth seeing why:

```
arrived from the world (through the door)  →  a moment dates it
created by a rule (inside the machine)     →  the rule's own record explains it
```

Those answer different questions. *When did this reach me?* only makes sense for
something that reached you. A node a rule derived didn't arrive from anywhere;
what you want to know about it is what made it, and that's already recorded.

## No rule ever calls the clock

Notice what none of the above asked an author to do.

There is no line in any rule that says *stamp this*. The moment is minted at the
one place the world is touched — the door from Chapter 12 — and everything
downstream just finds things dated.

That's a concern **woven in**, not written down. Transactions are woven the same
way: four hand-placed sites, and no rule mentions them either.

The machine deliberately has no general mechanism for this yet, and the reason
is a good example of when *not* to build something. The two concerns weave at
different places — one at an *action* crossing to the outside, the other at a
*program* starting and ending — so a general mechanism would first have to
invent a vocabulary of places-to-weave-at. That's a design, not a tidy-up. What
is already known is its shape: a table the machinery consults and does not fill
in. What must never happen is machinery that knows what a timestamp *is*.

## Even an arrow can be dated

Chapter 1 mentioned that arrows have identities of their own. This is what that
buys:

```
a moment dates the arrow shelf ─jar→ pepper  : True
what points at that arrow                    : the moment
```

*When did this jar appear on this shelf?* is a question about the **connection**,
not about either end, and until edges had identities there was nowhere to put
the answer. The reverse index needed no change at all: it's keyed by whatever is
pointed at, and an arrow is now something that can be pointed at.

---

**Next:** the machine is not the only one talking.
[Who said it →](30-who-said-it.md)

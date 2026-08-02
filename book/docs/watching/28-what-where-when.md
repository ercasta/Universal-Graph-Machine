# What, where, and when

Chapter 3 taught the machine three answers: *yes*, *no*, and *I don't know*. Every
question since has been one of those, dressed up.

These three are different, and the difference is easy to miss. *Where is the
parcel?* has a **gap** in it. You aren't offering a claim for the machine to
check; you're asking it to fill in a blank.

It turns out that needs almost nothing built — but the "almost" is real, and it's
the last genuine gap this project found.

## A parcel in a box in a warehouse

The parcel is in the box. The box is in the warehouse. Is the parcel in the
warehouse?

Obviously yes. And the machine could not say so.

```
is the parcel directly in the warehouse?      false
is the parcel in the warehouse, any depth?    true
```

The first answer isn't wrong — there is no arrow from warehouse to parcel — but
it's useless. And nothing in the machine could express the second. A type reaches
a fixed number of arrows deep (Chapter 21). A constraint checks one link. The
path language of Chapter 21 had no way to say *keep going*.

This one item was reached twice, independently: once by testing five relational
ideas against the machine's existing vocabulary and finding four of them were
already expressible in disguise, and once by asking what the word *where*
requires. Both landed on **transitivity**, alone.

So `contains+` was added: *follow this arrow as many times as it takes*.

!!! warning "As a question only — never as a way of naming something"
    *Is X reachable from Y?* stays a yes-or-no question about two things you
    already have, so it breaks nothing.

    But writing `box.contains+.label` as a **name** for something would be a
    different beast: it denotes a **set**, and everything in this machine that
    resolves a name promises one node or nothing. So the path language still
    refuses the `+` there — and, importantly, says where to go instead. That's
    the difference between a refusal and a dead end.

**And a reach goal can be planned for**, which is the part a yes-or-no answer
doesn't give you for free. Tell the machine to get the parcel into the warehouse
without touching the warehouse itself, and it works out that putting the parcel
in the box will do — even though the rule that does it establishes *box contains
parcel*, which is not the constraint it was asked about.

That works only because of Chapter 7's rule that **ranking never filters**. The
closing move can't reach the top band, so it's found by being ranked plausible
rather than proved relevant. Had relevance been a filter, this goal would have
been unreachable — a rule written long before this case existed, earning its keep
in a case its author hadn't imagined.

!!! note "A termination guard is tested by a question that fails"
    Containment is only *supposed* to be a tree; nothing in a graph enforces it.
    So reach carries cycle protection — and the first test of it was worthless.

    Asking whether something that **is** there is reachable returns before the
    loop can ever come round again. A version with **no cycle protection at all**
    passed. The check now asks for something that *isn't* there, because only a
    miss walks the whole cycle, and the unprotected version dies as it should.

## Three readers

With reach in place, three questions need a **verb** and nothing else:

| ask | it reads | machinery it needed |
|---|---|---|
| `what` | which declared shapes this satisfies | none — Chapter 21's recognition |
| `where` | what holds it, at any depth | reach, walked backwards |
| `when` | what it precedes, follows, or spans | comparisons on two numbers |

Write them the same way you write everything else:

```
where it is:
    parcel
```
```
parcel is in: box, wh   (nearest first)
```

```
what it is:
    parcel
```
```
parcel is: thing
```

```
when it was:
    inspect
```
```
inspect at 3-4; before ship; before paint; during build
```

**Nearest first, and not a set.** *Where is the parcel* has no single answer — it
is in the box **and** in the warehouse — so the answer is a list, in order of how
close each container is. A set would have thrown that ordering away, and this
project has been bitten by exactly that before.

!!! note "They are a different kind of question, not a fifth thing to do with one"
    Chapter 9's `goal`, `ask`, `why` and `plan` all state a whole proposition and
    differ only in what you want *done* with it. The obvious move was to add
    `what` as a fifth verb on the same body.

    It isn't one. These have a gap, and answering one is not searching for
    anything — it's locating a thing in an order the world already has. So they
    take a different shape (one bare name), and they **answer** rather than
    record.

## A reader records nothing

Here's the property worth the chapter, and it is Chapter 27's rule applied to
answers.

Ask *where is the parcel* twice and you get the same sentence, and the world is
byte-for-byte unchanged. Nothing was stored. Then move the parcel:

```
where it is:
    parcel
```
```
nothing here holds parcel
```

The answer **follows the world**, because there was never an answer sitting
anywhere to go stale. *Keep what you cannot re-derive* — and a reader's answer is
one traversal away at any moment, so storing it could only ever let it drift from
the thing it describes. This machine has been bitten by that exact drift before:
a stamp that still said `car` after the wheel came off.

!!! warning "The bug a weaker test would have passed"
    Plant a cache — have the reader quietly remember its answers off to one side.

    *Does asking change the world?* stays **green**: nothing was written to the
    graph. The answers still look right. Only one key goes red — *does the answer
    follow the world when it moves?*

    A test asserting only that asking is harmless would have shipped the bug.
    The property is not "asking writes nothing"; it's "there is nothing to go
    stale".

And this is not in tension with Chapter 3, where a settled answer *is* kept. A
derivation **ran**, and repeating it costs a search. Recomputing beats
remembering exactly when recomputing is cheap — and for a reader it always is.

What does reach the machine's memory is the **question**. That it was asked is
history. The answer never is.

## The word is content; only the traversal is machinery

One detail keeps a domain word from leaking into the engine.

`where` walks `contains` by default, because that's a common convention — but
plenty of worlds write the relationship the other way round, as `part_of`
pointing from the part to the whole. So a question can name its own hop, written
as it's walked *from the thing you're asking about*:

```
where it is:
    by part_of
    wheel
```

Same traversal, opposite convention, one answer: `hub, car`. Without that,
`where` would be about **containment** — a domain idea — instead of about
**reach**, which is a structural one.

!!! note "`when` earns nothing, and that's checked rather than argued"
    There's a famous list of thirteen ways two intervals can relate — before,
    meets, overlaps, during, and so on. It looks like a capability.

    It's eleven comparisons on four numbers, and it adds nothing a Chapter 21
    type couldn't already demand. That claim used to be an argument; now the same
    judgement is written **twice** — once as `when`, once as an ordinary authored
    type whose rule says `first.end < second.start` — and the two must agree.

    The first version of that check was wrong and the *type* was right: `<` is
    strict, so it means `before` and **not** `meets`, and two events that touch at
    a shared instant fall on the other side of the line. Three pairs now straddle
    that boundary in both directions, which is a much better test than the one it
    was meant to be.

    A point is just an interval whose ends coincide, which is what keeps *when
    did it happen* and *how long did it last* one question instead of two. And
    **incomparable is a third answer**: an event dated `"tuesday"` is not before
    one dated `3`, not after it, and saying so beats inventing an order between
    two vocabularies.

---

**Next:** so far the machine has looked inward. Now the clock, the other people,
and the things it has to wait for. [When things happened →](../world/29-when-things-happened.md)

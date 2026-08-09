# What it saw, and whether it was me

Chapter 13 gave the machine a record of what it was *thinking*. This chapter
gives it something different and, for an agent that shares its world with other
people, more urgent: a record of what it **looked at**, and when.

The two are not the same, and the difference is the chapter.

## A belief is not a sighting

The machine believes a directory holds three files. Ask it, and it says three.
Where did that come from?

It could be something it looked at a second ago. It could be something it looked
at an hour ago, before someone else emptied the folder. It could be something a
rule worked out and never checked. From the belief alone you cannot tell — and
neither can the machine.

So looking now records a second thing beside the belief:

```
the belief:      count = 0
what was seen:   count: 3 sighting(s), now 0
```

The belief stays exactly where it was, because everything reasons over it and
nothing should have to change. The sighting sits **beside** it, pointing inward
at the thing it is about — Chapter 13's rule, that memory points at the world
and never the reverse.

!!! note "Something never looked at has *no* sighting"
    Not a sighting saying "probably fine". Nothing at all. A folder the machine
    has never opened can hold a perfectly good `count: 99` in its belief and
    still answer:

    ```
    count: never looked at
    ```

    Manufacturing a sighting from the current value would destroy the only
    distinction this machinery exists to make — the same conflation as answering *no* when you
    mean *I didn't look* (Chapter 19).

And a sighting covers **every slot of the thing looked at**, not only the fields
that happened to change. *I checked this* means the whole state at that moment.
Recording only differences would make "unchanged" and "unobserved" the same
record, which is precisely the mistake one level down.

## Was it me?

Here is the question that makes the rest worth building.

The machine looks at the folder and finds 3. Later it looks again and finds 5.
Something changed. Was it the machine, or was it the world?

That matters enormously. *I emptied the folder* needs no explanation. *The folder
emptied itself while I was working* is news — it means somebody else is in here,
and half of what the machine believes may now be stale.

```
count: 3 sighting(s), now 0
  3 -> 5: external — nothing I did could have
  5 -> 0: mine (empty_it)
```

## The answer is worked out, not written down

The obvious design is a journal: every time the machine writes something, log it,
and later look up whether a change is in the log.

That design is broken in two directions at once.

**It misses the world entirely.** When a file appears on disk, *nothing happens
in the graph*. There is no write to log. The belief is simply wrong, silently,
until someone looks.

**And the look itself is a write.** So a naive journal records the machine
setting `count` from 3 to 5 and reports: *the agent changed it*. The truth is the
exact opposite — the agent **looked**, and found 5 where it had recorded 3.

So attribution is **derived** instead, from two things that already exist:

1. two sightings that differ, and
2. whether anything the machine actually did, between them, could have written
   that slot.

No new record. Nothing has to be maintained, so nothing can fall out of step.

## "Could have written it" is read off the rule

That second half is the good part, and it reuses Chapter 22 exactly.

`empty_it` is never told that it writes `count`. Nobody declared it. The machine
reads the stored body and works it out:

```
writes read off empty_it: {('attr', 'count', 'd', None)}
```

*It writes the attribute `count`, on whatever it was handed as `d`.*

Then it checks the bindings that were actually used — this rule, pointed at
*this* folder — and only then says *mine*. A rule that could have written the
slot but was pointed somewhere else does not get the credit.

!!! warning "It bounds change from below, and never counts it"
    Three sightings reading 3, then 9, then 3 prove **at least two changes**.
    They cannot prove there were exactly two rather than six. A round trip is
    visible when a look falls inside it and invisible when none does, which makes
    this a question about how often you look, not about what is knowable in
    principle.

    That is also why a sighting is recorded even when nothing changed. Collapse
    to "record only differences" and 3, 9, 3 becomes *no change* — the machine
    would have watched a round trip happen and filed it as nothing.

## Knowing that you're probably wrong

One useful number falls out for nothing. Count how many changes to a slot the
machine could **not** attribute to itself:

```
a slot other people touch: {'looks': 4, 'changes': 3, 'unattributed': 3, 'rate': 1.0}
a slot only I touch:       {'looks': 2, 'changes': 1, 'unattributed': 0, 'rate': 0.0}
```

That is **volatility**, and it gives *go and look* a second trigger it never had.

Up to now the only reason to check something was ignorance: *I don't know, so go
and find out.* Volatility supplies the reason that actually arises for an agent
whose world contains other people: **I do know, and it's probably stale.**

The vacuity guard matters here — a slot nobody else touches must score zero, or
"volatile" would just be a longer word for "observed".

## What this doesn't cover yet

Sightings hang on **attributes**, and an absent **edge** has nowhere to hang one.
So the machine can observe that a folder's `count` changed, but not directly
observe that its *contents* did.

The answer that already exists elsewhere in the machine is to be qualitative
about it — Chapter 10's expectations say "files appeared", never how many — and
the same coarseness is what belongs here. It's an honest gap rather than a
solved one.

---

**Next:** the machine has been running one thing at a time this whole book.
[One loop, and everything on it →](25-one-loop.md)

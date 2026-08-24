# Moments

There used to be a **moment**: the machine's construct for a state of affairs,
a signed delta plus a predecessor, chained into a history. A state in time was
a moment. A hypothetical was a moment. A rule's antecedent was a moment. There
was no separate "frame", "world", "context" or "scope" object anywhere in the
design — everything went through one construct.

There is no moment any more. This chapter is about what happened to it, and
what's here instead.

## What replaced it

> **One graph is the whole state.**

Nodes with ordered members, and one more relation on top: `believed`. A
proposition is believed when its anchor is present and not believed when it
isn't (Chapter 2). That's the entirety of what the machine knows *now* — and
"now" is doing a lot of work in that sentence, because there is exactly one of
it.

```
believed(mortal(paul))     present = believed
```

No predecessor. No delta this state was reached *from*. Nothing that says
what changed to get here, because nothing keeps a *here* to have gotten to —
there is one state, and asserting or erasing edits it in place.

## Why the chain went

It didn't go all at once. Two cuts, and it's worth knowing both, because the
first one was measured and the second was a different kind of argument.

**The first cut removed the locus.** An entry used to carry not just a sign
but a second time — *what moment this claim was about*, as distinct from *when
it was deposited*. That bought a real capability: revising a view of the past
was ordinary, the same act as any other claim. It also meant every read had to
ask two questions in a fixed order — latest locus, then latest deposit, with
*at-or-before* decided by ancestry rather than by depth, because supposing
forked the chain. Measured on a real fixture, before anything was done,
resolving reads this way was **86% of runtime**. The locus went, and Chapter 5
is that whole story.

**The second cut removed the rest of the chain** — the delta, the
predecessor, the sign stored on a claim, `anc`/`pred`/`in_delta`, the licence
recorded on every entry. This one wasn't a performance fix; it was a scope cut.
A moment-and-chain design buys a *history* — session save and resume, a
`--why` that walks a proof back to what it rested on, "what did I believe at
time T". All three depended on the same structure, and none of them shipped
in a form worth the weight of keeping it: `--why` and session replay are gone
from this repo's own command line (Chapter 0), and the honest statement of
where that leaves things is the machine's own:

> *There is one graph, one current state, and what it holds is all there is to
> print. A scratchpad the agent could reload is a memory system, and it will
> be built as one rather than fallen into.*

## What that means for time

Nothing here understands time, and nothing pretends to. `causes` — the
connective that used to mean *lands in a later moment* — is refused at load,
because there is no later moment for it to mean anything about. There is one
connective now, `implies` (Chapter 6), and it relates a state of belief to
another, not a moment to a later one.

If a corpus wants ordering, duration, "before" and "after", it builds that
itself, out of ordinary facts and ordinary rules — the same way it builds
anything else the engine doesn't have opinions about:

```
before(<sunrise>, <noon>)
during(<battle>, <siege>)
```

**Time is an open class.** Tying it to the engine was tried, and the argument
against keeping it tied is the same argument Chapter 8 makes about verbs in
general: a fact a corpus can write and a rule can read beats a primitive baked
into the loop, everywhere except the two or three places (Chapter 30) where
the floor genuinely has no honest alternative. Time isn't one of those places.

## What it costs, scored the way this design scores everything

| | a mutable world state | **moment = delta + predecessor** (gone) | **one graph, one `believed`** |
|---|---|---|---|
| not leaking | overwriting loses what it replaced | every difference was deposited, licensed and ordered | asserting mints, erasing deletes; nothing in between is kept |
| not lossy | history is gone | nothing was overwritten | history is gone, on purpose |
| readable | a lookup | a lookup, once the locus went | a lookup — the same one, with nothing else to ask |
| composable | two writers contend for one cell | appending was the only write | asserting is idempotent; two writers land the same anchor |

The middle column is real history, not a strawman — it's what this project
ran for a long time, and it's genuinely more capable in the one row that
matters most: *not lossy*. Giving that up is a stated trade, not an oversight,
and Chapter 34 is where the gap it leaves (no `why`, no session memory) is
written down plainly as a gap rather than argued away.

What's left is the smallest thing that could still be called "belief":
presence, checked against one graph, with nothing behind it to walk.

---

**Next:** what *is this true?* actually computes, now that there's no history
left to walk.
[The read →](05-the-read.md)

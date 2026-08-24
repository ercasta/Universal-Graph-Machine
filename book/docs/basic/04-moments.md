# Moments

There is no moment, no history, and no notion of *when* inside belief.

> **One graph is the whole state.**

Nodes with ordered members, and one more relation on top: `believed`. A
proposition is believed when its anchor is present and not believed when it
isn't (Chapter 2). That's the entirety of what the machine knows *now* — and
"now" is doing a lot of work in that sentence, because there is exactly one of
it.

```
believed(mortal(paul))     present = believed
```

Asserting mints the anchor. Erasing deletes it. There is no predecessor, no
delta this state was reached *from*, nothing that records what changed to get
here — there is one state, and asserting or erasing edits it in place.

## What that means for time

Nothing here understands time, and nothing pretends to. `causes` — a second
connective, meaning roughly *this holds independently of whether its cause
still does* — is refused at load: there's no separate "later" for that idea
to attach to. The one connective is `implies` (Chapter 6), and it relates a
state of belief to another, not a moment to a later one.

If a corpus wants ordering, duration, "before" and "after", it builds that
itself, out of ordinary facts and ordinary rules — the same way it builds
anything else the engine doesn't have opinions about:

```
before(<sunrise>, <noon>)
during(<battle>, <siege>)
```

**Time is an open class.** A fact a corpus can write and a rule can read beats
a primitive baked into the loop, everywhere except the two or three places
(Chapter 30) where the floor genuinely has no honest alternative. Time isn't
one of those places.

---

**Next:** what *is this true?* actually computes.
[The read →](05-the-read.md)

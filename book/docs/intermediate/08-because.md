# Because…

This is the chapter the book is named for, in spirit. A machine that works
things out is useful. A machine that can tell you *how* is trustworthy.

And the interesting part isn't the explaining. It's what the machine **refuses**
to explain.

## The answer already contains its reasons

Back to the pantry. Nobody has sealed anything; we ask whether the salt is
sealed:

```
YES - derived in 1 step(s) (1 step(s) considered)
yes, because:
  seal(j=salt)
```

You saw this in Chapter 3. What's worth understanding now is *where that
explanation came from*, because it wasn't generated.

By Chapter 7, an answer **is** a route: a path through imagined situations from
what the machine knows to what you asked about. The explanation is that route,
read out. Finding the answer and finding the explanation were the same act.

Which is why the machine can't give you a wrong explanation for a right answer.
There's no second system reconstructing a story from a trace, no summariser that
might paraphrase badly. There's one object, and you're being shown it.

## Then it can be asked *why*

Once something has actually been worked out and kept, you can ask:

```
why is the salt sealed?:
    salt.sealed = true
```

```
salt.sealed = True: because seal(j=salt) ran
```

Note the tense. Not *"here is how that could follow"* — **it ran**. The machine
is reporting its own history: an action that really happened, to that particular
jar.

That history lives in the machine's notes — the ones you saw at the end of
Chapter 0 — filtered to what genuinely *ran*. While searching, the machine
considers all sorts of moves it then abandons; if "why" looked at those, it
would answer with roads not taken. It looks only at what was really done.

## The three honest answers — and the fourth that would be a lie

Here's where the chapter earns its place. There are three situations, and
blurring them is how explanation becomes worthless.

**It was worked out here.** There's a real cause and the machine names it, as
above.

**It's true, but nobody here worked it out.** Perhaps you simply told the
machine:

```
holds, but nothing here derived it - it was given, not worked out
```

**It isn't true at all.** Then there is no "why", and the machine says so rather
than answering a question you didn't ask:

```
does not hold - there is nothing to explain (ask whether it could be derived instead)
```

Now the fourth behaviour — the one the machine deliberately does **not** have.

Take that middle case: something true, with no recorded history. The machine
*could* run a fresh search and find a way it might follow. That search would
usually succeed, and it would produce something that reads beautifully:

```
    because seal(j=salt) ran      ← a plausible story. Nobody did this.
```

That would be a lie. Not a small one: a perfectly-formed explanation for
something that never happened, indistinguishable from a true one. And the moment
a system manufactures plausible history, **every** explanation it gives becomes
untrustworthy — because nothing downstream can separate the manufactured ones
from the real ones.

So the machine says it doesn't know. *"It was given, not worked out."*

!!! warning "The distinction, in one line"
    *How could this be true?* and *how did this come to be true?* are different
    questions. The first is a search; the second is a memory. Answering the
    first while being asked the second is the most seductive failure available
    to a reasoning system, because the output looks better than the honest
    answer does.

## Why "because" and never "therefore"

The machine's explanations say *because X ran*. They don't say *X, therefore Y*.

That's a deliberate limit on the claim. What the machine actually knows is: this
action was applied, and afterwards this was true. That's causation in the only
sense it can honour — something it did, and what followed. It isn't claiming to
have proved a logical entailment, so it doesn't borrow the word for one.

A small matter of wording. It's also the difference between a machine that
reports what it did and one that dresses its history up as logic.

## Explanations you can act on

One last thing, and it points forward. These explanations aren't text — they're
the same graph objects as everything else. So the machine can *read its own
reasoning*, which supports things text never could:

- noticing that two of its own intentions wrote the same thing for unrelated
  reasons (Chapter 15);
- working out which parts of a plan rest on guesses rather than on knowledge;
- turning a sequence of things it did into a new named rule (Chapter 14).

An explanation you can only print is a courtesy. An explanation you can reason
about is a capability.

---

**Next:** we've been writing `goal`, `ask` and `why` at the machine all book.
Time to look at that language properly. [Talking to it →](09-talking-to-it.md)

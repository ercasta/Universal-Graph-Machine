# A machine that explains itself

Most computers are oracles. You ask, they answer, and you just have to trust
them. Type a question into a search box and you get back "42" with no way to see
how it got there.

The Universal Graph Machine is different. It *reasons* — and it can always show
its work. Let's watch it solve a crime.

## The case

Three suspects. Here's everything we know, written the way you'd tell a friend:

```
ada is a suspect
bo is a suspect
cy is a suspect

bo in library          # bo was in the library
ada is alibied         # ada has an alibi
```

And here's how a detective *thinks* — a few rules. The `?someone` is a
**stand-in for anybody**: a rule with `?someone` in it applies to every person
the machine knows about. Read the last line as *"anybody who is a suspect and
isn't cleared is the thief."*

```
?someone is innocent when ?someone in library
?someone is cleared when ?someone is innocent
?someone is cleared when ?someone is alibied
?someone is thief when ?someone is a suspect and ?someone is not cleared
```

Now we ask the machine to name the thief:

```
who is thief
```

## Watch it work

The machine doesn't grind through every fact it knows. It's **lazy on
purpose** — it only chases the leads the question actually needs. Here's every
step it takes:

1. **The question sets a goal:** find someone who *is the thief*.
2. **Which rule makes a thief?** → *"a suspect who is not cleared."* So the
   machine needs two things about a person: are they a suspect, and are they
   *not* cleared?
3. **Who are the suspects?** → ada, bo, cy. It checks each one.
4. **Is ada cleared?** ada is alibied → *cleared*. So ada is **not**
   "not-cleared." **ada is out.**
5. **Is bo cleared?** bo was in the library → *innocent* → *cleared*.
   **bo is out.**
6. **Is cy cleared?** The machine looks for any reason cy is cleared… and finds
   none. No alibi, not in the library. **It has no evidence cy is cleared** — so
   "cy is not cleared" holds.
7. cy is a suspect **and** not cleared → **cy is the thief.**

```
→ cy is thief
```

!!! note "Notice what it *didn't* do"
    It never bothered to work out every fact about this world — it never even
    asked whether ada owns a bicycle. It followed *only* the trail the question
    needed. That laziness has a name, **demand-driven reasoning**, and it's one
    of the machine's most important ideas. We'll come back to it.

## Now make it prove it

Here's the part other machines can't do. Ask:

```
why is cy the thief?
```

and the machine hands back its actual reasoning — this is real output, exactly
what it prints:

```
cy is thief  <- rule.?someone.is.thief
  cy is_a suspect  (given)
```

Read it top to bottom: *cy is the thief* — the `<-` means **"this follows
from"** — from the **thief rule** (`rule.?someone.is.thief`). And that rule
stood on a fact we handed it directly: *cy is a suspect* (`given` means "you
told me this; I didn't have to work it out"). Every conclusion the machine
reaches leaves a trail like this, and you can always pull on it.

## One more thing: it knows what it *doesn't* know

Step 6 hid something important. When the machine couldn't find evidence that cy
was cleared, it made a *choice*: treat "no evidence" as "not cleared." That's
called **closing the world** — assuming that whatever you can't prove is false.
It's how detectives (and databases) usually work.

But sometimes that's the wrong stance. Suppose a stranger, **zz**, wanders into
the story — someone the machine has never heard a single fact about. We ask:

```
is zz the thief?
```

With a **closed world**, the machine reasons "I have nothing on zz, so — no":

```
→ no
```

But if we tell it the clue list might be *incomplete* and it should **keep an
open mind**, the very same question gets a very different, more honest answer:

```
→ unknown
```

Not "no." Not a guess. **`unknown`** — *"I don't have what I'd need to decide."*
A machine that can tell the difference between *"I've proven it's false"* and
*"I just don't know"* is doing something most software never does.

That honesty — reasoning only as far as the evidence allows, and saying so —
is what the rest of this book is about.

[:material-play-circle: **Try the whole case live**](../playground/detective.md){ .md-button .md-button--primary }

Edit a clue, re-ask, and watch the steps change. Delete `ada is alibied` and ask
*who is the thief?* again — see what happens to ada.

---

**Next:** we'll open up the world the machine lives in — a world made of nothing
but dots and arrows. [The substrate →](01-the-substrate.md)

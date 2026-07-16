# Supposing

Every good detective does it. Halfway through the case, they stop and wonder:
*"Suppose the butler lied about being in the library. What follows?"* They chase
the idea through — not because they believe it, but to see where it leads — and
then set it aside, their real notebook unchanged.

The machine can do exactly this. It's called **supposing**, and it's how you
reason about things that *aren't* known to be true.

## Reasoning in pencil

Normally, everything the machine concludes is written in **ink** — real, committed
knowledge. Supposing is different. When you ask it to *suppose* something, it
writes that assumption in **pencil**, works out the consequences in the margin,
reads off what you wanted to know — and then, if you like, **erases the whole
thing**. Your real facts are never touched.

Here's a genuine run. Our world has bo (in the library) and ada (with an alibi).
We ask the machine to *suppose* a newcomer, dz, was in the library — and to tell
us whether dz would then be cleared:

```
suppose:   dz in library
question:  would dz be cleared?

→ confirmed
   (worked out in pencil:  dz is innocent  →  dz is cleared)
```

The machine entertained the idea, chained it forward — *in the library, therefore
innocent, therefore cleared* — and confirmed the prediction. And then the crucial
part:

```
back in the real world:   is dz cleared?   →  no (assumed)
```

Nothing stuck. dz isn't really cleared, isn't even really in the story. The
supposition was explored and erased, leaving the actual case exactly as it was.

## Three ways a supposition can turn out

When you chase an assumption to its conclusions, one of three things happens:

- **Confirmed** — the thing you predicted *does* follow from the assumption. (*If
  dz was in the library, dz would be cleared.*)
- **Refuted** — the assumption leads to the **opposite** of your prediction, a
  contradiction. (*Supposing that leads nowhere good.*)
- **Inconclusive** — the assumption settles the question neither way.

Each is useful. "Confirmed" tells you a scenario hangs together; "refuted" tells
you a scenario is impossible; "inconclusive" tells you you're still missing
something.

## Why pencil-and-ink matters

The magic is the **safety**. Exploring "what if the butler lied?" must not
accidentally make the machine *believe* the butler lied. If supposing polluted
your real knowledge, you could never explore a hypothesis without corrupting the
case. The pencil/ink split guarantees that a question of the form *"what would
follow if…?"* leaves *"what's actually true"* untouched — unless you explicitly
decide to commit the assumption to ink.

This is how the machine can consider possibilities, weigh scenarios, and reason
about the might-be — all without ever losing its grip on the is.

!!! note "A note on the playground"
    The little in-page playground focuses on the basics — facts, rules, and
    questions. Supposing is one of the machine's deeper powers; the example above
    is real output from the full engine. If you want to drive it yourself, it
    lives in the library as the `suppose` operation.

---

**Next:** clues rarely say *yes* or *no* — most whisper *probably*. How does a
machine hold a *maybe* without fooling itself? [Living in an uncertain world →](10-uncertain-world.md)

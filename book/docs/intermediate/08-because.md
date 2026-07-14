# Because…

We opened this whole book with a promise: a machine that reasons *and can always
show its work*. You've seen the trick in passing every time you typed `why`. This
chapter is about how it actually works — and why it might be the machine's most
important feature of all.

## Every conclusion remembers where it came from

Here's the key idea. When the machine derives a new fact, it doesn't just add the
fact to the graph and forget how it got there. It also records a little
**receipt**: *which rule fired, and which facts it stood on*. This bookkeeping has
a name — **provenance** — and the machine does it automatically, for every single
conclusion, all the time.

So the graph doesn't just hold *what* the machine believes. It holds *why* it
believes each thing. Nothing is an unexplained assertion.

## "Why" is just reading the receipts back

When you ask `why cy is thief`, the machine isn't inventing an explanation after
the fact, or dressing up its answer in nice words. It's **replaying the receipts**
— walking back through the conclusions that led here, and reading them out. Recall
the chained case from Part 1:

```
why bo is cleared
```

```
bo is cleared  <- rule.?someone.is.cleared
  bo is innocent  <- rule.?someone.is.innocent
    bo in library  (given)
```

Every line is a receipt. *bo is cleared* came from the cleared-rule; that rule
stood on *bo is innocent*; which came from the innocent-rule; which stood on the
one thing we simply told it — *bo in library*, marked `(given)`. The explanation
isn't a story *about* the reasoning. It **is** the reasoning, read back to you.

## Why this matters so much

Three reasons, and they're big ones.

**You can trust it.** An answer you can't inspect is an answer you have to take on
faith. An answer with a because-trail is one you can *check*. If the machine says
cy is the thief, you can follow the trail and satisfy yourself that the logic
holds — or catch it standing on a fact that's wrong.

**You can correct it.** When an explanation rests on a bad clue — *"…because bo in
library,"* but bo was actually in the cellar — you know exactly which fact to fix.
The machine even tells you which conclusions depended on it. Contrast that with a
machine that just says "cy is the thief" and offers nothing: when it's wrong, you
have nowhere to start.

**It can't bluff.** A system that generates confident-sounding text has no
built-in tether to the truth — it can be fluent and wrong. This machine's "why"
is not generated prose; it's a faithful record of steps it actually took. It can
be *mistaken* (if you fed it a wrong fact), but it cannot **bluff** — there's no
gap between what it did and what it says it did.

## No conclusion without a cause

Put the last few chapters together and a picture emerges. The machine only works
things out on demand (Chapter 6). It's honest about what it can't establish
(Chapter 5). And now: everything it *does* establish comes with a traceable
reason (this chapter). That's a strikingly honest way to think — it does the work
the question needs, admits the gaps, and shows the receipts for the rest.

??? info "Deep dive: the proof *is* the record"
    In the slice of logic this machine works in, the trail of receipts isn't
    merely *a* proof — it's *the* proof object itself. There's no separate,
    hidden "real" derivation that the `why` output approximates; the receipts the
    machine kept while reasoning are exactly the justification, rendered back into
    the language you speak. Explanation and proof are the same thing. The
    [appendix has a short note on provenance](../appendix/index.md).

## Try it

Ask `why` about several things in the playground. Ask `why cy is thief`. Then ask
`why bo is cleared` and watch a longer chain unfold. Try asking `why` about a fact
you simply *stated* (like `why bo in library`) and see the trail bottom out at
`(given)` — the machine's way of saying *"because you told me so."*

[:material-play-circle: **Open the playground**](../playground/detective.md){ .md-button .md-button--primary }

---

## End of Part 2

You now understand *how the machine thinks*: why it's lazy, how it tells "no" from
"I don't know," the careful little language it speaks, and how it justifies every
step. That's the working mind, fully open.

**Part 3 — Advanced** goes further out: reasoning about things that *aren't* true
(yet), untangling when two names mean one person, gathering evidence it doesn't
have, and — at last — a look at the tiny machine humming underneath it all.

[Begin Part 3 → Supposing](../advanced/09-supposing.md)

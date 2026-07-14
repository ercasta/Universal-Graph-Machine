# Only chase what you need

We've called the machine "lazy on purpose" since Chapter 0. This chapter pays
that off — because its laziness is not a shortcut, it's a whole *philosophy* of
how to think, and it has a surprising payoff.

## Two ways to reason

Imagine you've just been handed a thick case file and one question: *who's the
thief?* You could work two ways.

**The eager way.** Start from the file and work out *everything* you possibly
can. Who's innocent, who's cleared, who was where, every consequence of every
clue — grind until no new fact can be squeezed out. Now the answer to *any*
question is already sitting in your notes. This is called reasoning to a
**fixpoint** ("keep going until nothing changes").

**The lazy way.** Start from the *question* and chase only the threads it needs.
To find the thief you need to know who's a suspect and who's not cleared — so you
check exactly that, and nothing else. You never work out who owns a bicycle,
because nobody asked. This is **demand-driven** reasoning, and it's the machine's
normal mode.

## Watch the laziness

You've already seen it. When you ask `who is thief` in the playground and watch
the step view, the machine checks each suspect's *cleared* status — because the
thief rule demands it — and then stops. It never wonders whether ada is nervous,
or where cy keeps her keys. Those facts are *derivable*, but nobody demanded
them, so they're never derived.

That's the difference in one picture: the eager machine fills the whole
notebook; the lazy machine writes only the lines its question needs.

## Why lazy usually wins

In a real knowledge base, "everything you could possibly conclude" is enormous —
often far larger than the facts you started with. Computing all of it to answer
one small question is a colossal waste. Demand-driven reasoning does the little
slice of work the question actually requires, and skips the rest. For most
questions, most of the time, that's dramatically less effort.

!!! note "So why keep the eager way at all?"
    Sometimes you genuinely want *everything* worked out at once — to export a
    complete picture, to inspect the whole world, or to hand a finished snapshot
    to another tool. The machine can do that too, on request. But it's the
    exception; asking a question is the rule, and a question is lazy by default.

## The surprising bonus: honest ignorance

Here's the payoff that makes laziness more than an optimization. Because the
lazy machine only ever looks *as far as a question demands*, it always knows
**how far it looked** — and can tell you when it looked as hard as it could and
still came up empty.

That's the deep reason it can say **unknown** honestly (Chapter 5). An eager
machine that has already computed "everything" has no natural way to express *"I
didn't find it, but I might not have looked everywhere"* — it believes it looked
everywhere. The lazy machine, chasing a specific goal to exhaustion, can
distinguish *"I chased this down and it's genuinely not there"* from *"I ran out
of time/budget before I finished"* — and report the difference instead of
guessing.

Laziness, in other words, is what lets the machine be **honest about the edges of
its own knowledge**. Thinking only about what you're asked turns out to be not
just efficient but wiser.

??? info "Deep dive: the names for these"
    In computer science the lazy, question-first style is often called *backward
    chaining* (you reason backward from the goal); the eager, work-it-all-out
    style is *forward chaining*. UGM's demand-driven engine is a refined backward
    method (it remembers what it has already been asked, so it never chases the
    same thread twice). The [appendix has a gentle
    comparison](../appendix/index.md#demand-driven-vs-fixpoint-why-the-machine-is-lazy).

## Try it

Ask a question in the playground and watch the step view: notice how *few* things
the machine actually checks. Then ask a different question about the same world
and see it chase a *different* set of threads. Same facts, same rules — the
question decides what gets thought about.

[:material-play-circle: **Open the playground**](../playground/detective.md){ .md-button }

---

**Next:** we've been writing facts and questions in a peculiar near-English all
along. Let's look at the language itself.
[Talking to the machine →](07-controlled-language.md)

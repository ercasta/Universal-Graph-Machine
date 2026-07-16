# Living in an uncertain world

A detective's world is rarely tidy. Most clues don't announce *yes* or *no* —
they whisper *probably*. The witness was *likely* nervous. The suspect is
*probably* left-handed. A good detective neither throws these half-facts away nor
pretends they're certain. They hold them as **possibilities**, weigh them, and
stay honest about which is which.

Back in Chapter 5 the machine had three answers: **yes**, **no**, and **I don't
know**. This chapter adds the ones *in between* — **likely**, **unlikely**, and
their cousins — and, more importantly, the discipline that keeps them honest.

## A fact you're only half-sure of

You can tell the machine something *hedged*:

```
sam is likely a spy
```

The machine doesn't file this as a plain fact. It opens a little **possible
world** — sam-the-spy — and tags it with *how possible* it is. Then, asked the
obvious question, it answers in kind:

```
is sam a spy    →  likely
is sam a monk   →  no
```

Notice the honesty on both lines. It won't say a flat *yes* to the spy question —
it only has a hedge, so it gives you back a hedge. And for the monk it has nothing
at all, so it falls back to the ordinary defeasible *no* from Chapter 5. The full
range of answers now runs **certain · very likely · likely · unlikely · very
unlikely · no · unknown** — a dial, not a switch.

## Doubt travels

Here's the part that makes it *reasoning* and not just labelling. Chase a hedge
through a chain of rules and the doubt comes along for the ride:

```
sam is likely a spy
   ?p is watched when ?p is a spy
   ?p is nervous when ?p is watched

is sam watched   →  likely
is sam nervous   →  likely
```

Because the whole chain hangs off a single *likely* fact, every conclusion down
the line is only *likely* too. A chain is exactly as strong as its **weakest
link** — reason through a maybe, and you get a maybe. The machine never quietly
launders a hunch into a certainty three steps later.

## The honest jump — and a dial for it

Now the interesting case: a rule that *leans on a doubt*. Suppose sam is a surgeon,
and — going only on a lazy prior — the machine half-believes surgeons aren't women:

```
sam is a surgeon
sam is unlikely a woman
   ?p is flagged when ?p is a surgeon and ?p is not a woman
```

Should the machine flag sam? That depends on how boldly you let it jump to
conclusions — and *you set the boldness*:

```
decisive setting   →  is sam flagged:  likely
cautious setting   →  is sam flagged:  no
```

Two things are worth pausing on. First, on the **decisive** setting it *does*
make the leap — but it says **likely**, not *yes*. It knows the jump rests on an
assumption that could be wrong, so the conclusion wears its doubt out in the open.
Second, on the **cautious** setting it simply **refuses**: while it's even a
little possible that sam *is* a woman, it won't lean on "not a woman."

That single dial is the machine's answer to jumping-to-conclusions. This is the
old surgeon riddle — *the surgeon said "I can't operate, he's my son"* — the trap
being the silent assumption that a surgeon is a man. This machine can make that
guess, but never silently: the guess is a visible *likely*, and how far it's
willing to guess is a knob you control, not a bias baked in the dark.

## Keeping possibilities paired

Some doubts come in matched sets. "sam is either tall and quiet, or short and
loud" isn't four separate maybes — it's *two whole scenarios*, and the pairing
matters:

```
sam is either tall and quiet or short and loud

is sam tall    →  likely
is sam quiet   →  likely
is sam short   →  likely
is sam loud    →  likely
```

Each side is a live possibility — a coin-flip the machine hasn't resolved, so it
reports every option as open. But watch what it **refuses** to do: mix the two
scenarios. Ask it to reason from *tall* (scenario one) *and* *loud* (scenario two)
at once —

```
   ?p is impossible when ?p is tall and ?p is loud

is sam impossible   →  no
```

— and it declines flatly. Tall-and-quiet and short-and-loud can't both be true, so
a conclusion that needs *tall* from one and *loud* from the other stands on
nothing. The machine tracks which scenario each maybe belongs to and will not
secretly stitch two incompatible worlds together to reach a conclusion. That's the
difference between weighing possibilities and fooling yourself with them.

## It's all still pencil

None of this touches what the machine actually *believes*. Every possibility here
lives in **pencil** — the same pencil from [Supposing](09-supposing.md). A hedge,
a scenario, a doubtful jump: all of them are entertained in the margin, weighed,
and read off, while the **ink** — the machine's committed knowledge — stays exactly
as it was. That's what lets the machine live in an uncertain world without losing
its grip on the certain one: it can hold a dozen maybes at once, rank them, chase
them, reject the impossible combinations — and still tell you, cleanly, the
handful of things it actually *knows*.

!!! note "A note on the playground"
    The in-page playground sticks to the basics — plain facts, rules, and
    questions. Likeliness is one of the machine's deeper powers, layered on top of
    supposing; the runs above are real output from the engine. If you want to drive
    it yourself, it is a firmware stance: author forks with `add_fork` (or the hedge
    CNL), then ask through the ordinary engine under
    `FirmwarePolicy(uncertainty="banded")` — the same questions, graded answers.

Curious how a "likely" is actually stored and carried? Part 4 opens the hood:
[Shades of maybe →](../deep/uncertain-world-internals.md).

---

**Next:** clues don't only whisper *probably* — they also say *more* and *less*.
How does the machine rank suspects it has never measured?
[More or less →](more-or-less.md)

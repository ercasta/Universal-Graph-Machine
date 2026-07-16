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

The witness thinks — *thinks* — cy looked jittery. You can tell the machine
exactly that, hedge and all:

```
cy is likely nervous
```

The machine doesn't file this as a plain fact. It opens a little **possible
world** — nervous-cy — and tags it with *how possible* it is. Then, asked the
obvious question, it answers in kind:

```
is cy nervous   →  likely
is cy a monk    →  no
```

Notice the honesty on both lines. It won't say a flat *yes* to the nervous
question — it only has a hedge, so it gives you back a hedge. And for the monk it
has nothing at all, so it falls back to the ordinary defeasible *no* from
Chapter 5. The full range of answers now runs **certain · very likely · likely ·
unlikely · very unlikely · no · unknown** — a dial, not a switch.

## Doubt travels

Here's the part that makes it *reasoning* and not just labelling. Chase a hedge
through a chain of rules and the doubt comes along for the ride:

```
cy is likely nervous
   ?p is jumpy when ?p is nervous
   ?p is suspicious when ?p is jumpy

is cy jumpy        →  likely
is cy suspicious   →  likely
```

Because the whole chain hangs off a single *likely* fact, every conclusion down
the line is only *likely* too. A chain is exactly as strong as its **weakest
link** — reason through a maybe, and you get a maybe. The machine never quietly
launders a hunch into a certainty three steps later.

## The honest jump — and a dial for it

Now the interesting case: a rule that *leans on a doubt*. Back to the case. Cy is
a suspect, and cy's alibi is… shaky — someone *vaguely* remembers vouching for
them:

```
cy is a suspect
cy is unlikely alibied
   ?p is thief when ?p is a suspect and ?p is not alibied
```

Should the machine accuse cy? The rule needs "*not* alibied" — but the alibi
isn't absent, it's *unlikely*. Whether that counts depends on how boldly you let
the machine jump to conclusions — and *you set the boldness*:

```
decisive setting   →  is cy thief:  likely
cautious setting   →  is cy thief:  no
```

Two things are worth pausing on. First, on the **decisive** setting it *does*
make the leap — but it says **likely**, not *yes*. The accusation rests on
dismissing a shaky-but-real alibi, so the conclusion wears that doubt out in the
open. Second, on the **cautious** setting it simply **refuses**: while it's even
a little possible that cy *is* alibied, it won't lean on "not alibied."

That single dial is the machine's answer to jumping-to-conclusions — the same
trap as the old surgeon riddle (*"I can't operate, he's my son"* — the silent
assumption that a surgeon is a man). This machine can make that kind of guess,
but never silently: the guess is a visible *likely*, and how far it's willing to
guess is a knob you control, not a bias baked in the dark.

And the honesty carries into the round-up questions too. Ask *who*, and every
name in the answer carries its own confidence:

```
who is thief        →  cy is thief (likely)
is anyone thief     →  likely
```

A suspect the machine could convict *outright* would be listed plainly; cy comes
with the hedge attached. No flat accusations on shaky evidence — even in a list.

## Keeping possibilities paired

Some doubts come in matched sets. Two witnesses caught a glimpse of the intruder
and disagree: one saw someone *tall and quiet*, the other someone *short and
loud*. That isn't four separate maybes — it's *two whole scenarios*, and the
pairing matters:

```
intruder is either tall and quiet or short and loud

is intruder tall    →  likely
is intruder quiet   →  likely
is intruder short   →  likely
is intruder loud    →  likely
```

Each side is a live possibility — a coin-flip the machine hasn't resolved, so it
reports every option as open. But watch what it **refuses** to do: mix the two
testimonies. Ask it to reason from *tall* (witness one) *and* *loud* (witness
two) at once —

```
   ?p is impossible when ?p is tall and ?p is loud

is intruder impossible   →  no
```

— and it declines flatly. Tall-and-quiet and short-and-loud can't both be true,
so a conclusion that needs *tall* from one story and *loud* from the other stands
on nothing. The machine tracks which scenario each maybe belongs to and will not
secretly stitch two incompatible worlds together to reach a conclusion. That's
the difference between weighing possibilities and fooling yourself with them.

## It's all still pencil

None of this touches what the machine actually *believes*. Every possibility here
lives in **pencil** — the same pencil from [Supposing](09-supposing.md). A hedge,
a scenario, a doubtful jump: all of them are entertained in the margin, weighed,
and read off, while the **ink** — the machine's committed knowledge — stays exactly
as it was. That's what lets the machine live in an uncertain world without losing
its grip on the certain one: it can hold a dozen maybes at once, rank them, chase
them, reject the impossible combinations — and still tell you, cleanly, the
handful of things it actually *knows*.

!!! note "Try it live"
    All the runs above are real engine output — and you can drive them yourself:
    [the uncertain case](../playground/uncertain.md) puts the whole detective
    world in your browser, shaky alibi, glimpsed getaway, cautious/decisive dial
    and all. (For the library-minded: it's a firmware stance —
    `FirmwarePolicy(uncertainty="banded")` — and the same questions come back
    with graded answers.)

Curious how a "likely" is actually stored and carried? Part 4 opens the hood:
[Shades of maybe →](../deep/17-uncertain-world-internals.md).

---

**Next:** clues don't only whisper *probably* — they also say *more* and *less*.
How does the machine rank suspects it has never measured?
[More or less →](11-more-or-less.md)

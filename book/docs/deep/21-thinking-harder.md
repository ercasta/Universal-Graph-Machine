# Thinking harder

Back in [Chapter 18](18-modes.md) we let a phrase slip by with barely a comment:
eight of the nine ways of thinking **spend effort**, and *"think harder" means
more of it.* That sounds like a throwaway line about speed. It isn't. It's one of
the most important honesty features in the whole machine — and it's worth a chapter
of its own.

## Reasoning on a budget

Here is the plain fact. When the machine chases a question, it does not get to
think forever. It works in **rounds** — each round follows the trail one notch
further — and it starts with a **budget** of rounds. If the answer is close, a
handful of rounds reaches it with budget to spare. If the answer sits at the end
of a long chain of reasoning, the budget can **run out** before the machine gets
there.

Why on earth build in a limit? Because the alternative is worse. A reasoner with
no budget, handed a question it can't settle, doesn't fail *cleanly* — it wanders,
or spins, or quietly gives you whatever half-finished guess it happened to be
holding when something else interrupted it. The budget turns "I might think about
this forever" into "I will think about this *this hard*, and then tell you where I
got to." It's the difference between a colleague who says *"I ran out of time, but
here's how far I looked"* and one who never comes back from the archives.

## The honest part: it knows when it didn't finish

Now the piece that makes this more than a stopwatch. When the budget runs out mid-
chase, the machine **notices**. It doesn't mistake *"I didn't finish looking"* for
*"there's nothing there."* Those are wildly different claims, and conflating them
is how confident systems tell confident lies.

So a question cut short by the budget comes back as **`unknown`** — the same honest
shrug you met in [Chapter 5](../intermediate/05-no-and-unknown.md), arriving now
for a new reason. In Chapter 5 the machine said `unknown` because evidence was
*missing*. Here it says `unknown` because its *looking was unfinished*. Both are
the same refusal: it will not upgrade *"I don't know yet"* into a decided answer it
hasn't earned.

That's the whole trick, and it's why a bounded reasoner is *more* trustworthy than
an exhaustive one, not less. A machine that must run to completion before it will
speak has to pretend completion is always possible. This one doesn't pretend. It
tells you the shape of what it managed: *"I looked this far, along here, and time
ran out."*

## Watch it happen — the hard case

Take the detective world one turn harder. This time **ada** has a real alibi, but
a *deep* one — a **chain of vouching witnesses**. Only **vic** has a rock-solid
alibi: she was **onstage**, in front of the whole audience. From there, clearance
has to *travel*: vic vouches for **uma**, uma for **rex**, rex for **sam**, and sam
for **ada**. Four hops back to the stage before the machine can rule ada out.
**bo**, by contrast, is vouched for *directly* by an anchored witness — one hop.
And **cy** has nobody.

Ask **`is ada thief`** on a small budget:

> **unknown** — *the machine set off along ada's alibi, traced a witness or two, and
> ran out of budget before it reached the stage. It won't guess.*

Now hand it a bigger budget — *think harder* — and ask again:

> **no** — *this time it followed the chain all the way: vic (onstage) → uma → rex →
> sam → ada. Her alibi holds. She isn't the thief.*

The bigger budget didn't *change* anything about ada. It only let the machine
**finish** a walk it had already started correctly. The answer it reaches with more
thinking is one it would always have reached — the small budget just couldn't get
there.

## The sharpest lesson: taking back a hasty accusation

The prettiest demonstration is the round-up question, **`who is thief`**.

On a small budget, the machine can't finish clearing ada — and look what that does.
To call someone a thief it needs them *not cleared*, and since it never *finished*
establishing ada's clearance, a quick glance leaves her looking guilty. So it
**over-accuses**: it names *ada and cy*. A hasty round-up sweeps up an innocent
person, exactly the way a hurried mind does.

Give it room to think, and it **takes the accusation back**. The alibi checks out,
ada drops off the list, and the machine names only **cy**. Same facts, same rules —
the only thing that changed is that it thought it through before speaking.

If you've ever watched someone leap to a conclusion because they hadn't followed a
detail to the end, you know this failure. What's unusual here is a *machine* that
can tell the two states apart — *"I've cleared her"* versus *"I haven't finished
checking"* — and won't let the second masquerade as an accusation.

## Why the budget lives outside the reasoning

Notice where the dial sits. The budget isn't wired into any particular rule, and
it isn't part of what the facts *mean*. It's a setting **handed to** the reasoner
from outside — a sibling of the swappable *attitude* from
[Chapter 20](20-firmware.md). "Open-minded or closed," "cautious or decisive," and
"how hard to think" are all knobs on the *stance*, not surgery on the *engine*.
That's why turning the dial can never corrupt an answer: the machinery underneath
is identical; it simply gets to run longer.

And it's why this is the natural close to the machine's story. The whole book has
argued for a reasoner that **shows its work and knows its limits** — that says
*because…* when it's sure, *no, for now* when it's guessing, and *unknown* when it
genuinely can't tell. "Think harder" is that same honesty pointed at effort itself:
the machine treats *"I ran out of time"* as a real, reportable answer, never as an
excuse to make one up.

That's an agent, not an oracle. An oracle claims to have seen everything. An agent
looks as hard as it can, and is honest about where it stopped.

---

## The end of Part 4

You've now seen the machine all the way down: a dumb, uniform substrate; a small,
generic engine; nine ways of thinking; a thin layer of declared attitude; and a
budget it spends honestly. There genuinely is nothing left hidden — including the
one thing most systems hide hardest, *how much they actually looked*.

- Try it yourself in [**the hard case**](../playground/harder.md) — tick *think it
  through* and watch an `unknown` become an answer.
- The [appendix](../appendix/index.md) collects every concept, including the full
  [instruction set](../appendix/index.md#the-instruction-set-the-data-path) and the
  [nine modes](../appendix/index.md#the-nine-processing-modes) as reference tables.
- The project — code, design notes, and all — lives on
  **[GitHub](https://github.com/ercasta/Universal-Graph-Machine)**.

[:material-play-circle: **Open the hard case**](../playground/harder.md){ .md-button .md-button--primary }

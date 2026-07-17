# Paying attention

Back in Chapter 6 the machine learned to be lazy on purpose: chase only the
threads a question needs. That answered *what* to think about. This chapter
answers the other half — **where to look** — because a long investigation has a
problem laziness alone doesn't solve.

## The desk and the archive

Picture a detective three months into the job. Every case they've ever worked is
in the room: boxes of clues, old suspects, closed files. If they re-read the
*entire archive* every time someone asks a question about the *current* case,
they get slower with every case they close — not because today's case grew, but
because the room did.

A real detective doesn't work that way. They keep one case file **open on the
desk**, and that's what they think with. The archive stays — nothing is thrown
away — but it isn't *in mind*.

The machine has exactly this: a **working set** (we call it the **focus**). It's
a small, visible list of who and what is currently *in play*. Everything else
the machine knows is still there, still true, still answerable — just not on the
desk.

## What lands on the desk

Mostly, you don't manage the focus — it follows the conversation:

- **Mention someone and they're in play.** Say `cy is nervous` or ask
  `is cy cleared`, and *cy* joins the working set. That's the implicit rule:
  talking about something is what puts it on the desk.
- The desk holds **individuals, not categories**. When you ask about cy, *cy*
  enters the focus — not *suspect*. A shared category would quietly drag every
  suspect from every old case back onto the desk, and the whole point would be
  lost.

And when the *topic* changes, you say so — in the same plain language as
everything else:

```
focus on the warehouse case      ← open a new file (a fresh focus frame)
forget that                      ← close it; back to the previous file
back to cy                       ← reopen the file cy is in
```

These are ordinary recognized lines, not commands in a different language. A
topic switch is **explicit** — the machine never guesses that you changed the
subject, because a wrong guess would silently make it forget the right things.
If a stray mention cluttered the desk, `forget that` tidies it; you can always
see the working set, so there's nothing hidden to go wrong.

## Thinking inside the file

Here's the payoff. When the machine answers *with bounded attention*, it reasons
only within the focus and what connects to it: a fact takes part in the thinking
only if it touches something on the desk.

The effect on a long session is dramatic. In one of our measurements, a machine
that re-read the whole archive on every question slowed from half a second to
nearly two *minutes* per question as closed cases piled up. The same machine,
answering from the open case file, stayed under a tenth of a second — flat, no
matter how big the archive grew. The cost of a question tracks **the case, not
the career**.

## An honest trade, out in the open

Careful, though — this is not a cache or a speed trick that "just works." It's a
*stance*, and the machine is honest about it:

**A focused answer can differ from an archive answer.** If the clue that clears
cy is sitting in a closed file that nothing on the desk touches, the focused
machine won't see it — exactly like the detective who hasn't re-read last
year's boxes. Ask the same question over the whole archive and you'll get the
fuller (slower) answer.

Neither mode is "the right one." Attention is how real agents afford to think at
all; the whole archive is what an audit wants. So the machine doesn't choose —
**the system using it chooses, per question**: work the case, or sweep the
archive. What matters is that the boundary is explicit and inspectable, never a
silent approximation.

!!! note "The desk is also what pronouns mean"
    The working set earns its keep twice. Whoever translates loose human talk
    into the machine's language ("*he* was lying — check *his* alibi") can ask
    the machine who is currently in play, and resolve *he* against that. The
    focus **is** the conversation's who-are-we-talking-about, exposed as plain
    data instead of buried in a language model's intuition.

## Closing a file really closes it

One more piece of housekeeping falls out. A conversation leaves scaffolding
behind — goals you set, tool calls in flight, the machinery of the discussion
itself. When you leave a topic (`forget that`, `back to X`), the machine sweeps
the *scaffolding* of what you left: the stale goals and pending calls of a
closed case don't linger to fire again months later.

The **facts never go**. Clues are permanent — reasoning never deletes what you
learned (a promise the internals chapters make precise); only the
*conversation's own apparatus* is cleaned up. Close the file, keep the evidence.

---

**Next:** the machine stops merely *answering* and starts *doing* — following a
routine, planning around gaps, and coping when the world doesn't deliver.
[Getting things done →](15-getting-things-done.md)

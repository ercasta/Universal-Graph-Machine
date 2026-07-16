# More or less

Detectives rank things all the time without ever measuring them. *Cy is more
suspicious than Ada.* Nobody has a suspicion-meter — there's no number behind
that sentence, just an ordering. And orderings have a famously slippery habit:
they don't always tell you everything. If cy outranks ada, and dan outranks bo,
who outranks whom between cy and dan? Maybe nobody knows. A machine that
*pretends* to know would be lying.

This chapter is about comparisons: how the machine holds them, chains them, and
— just as important — when it refuses to answer.

## Saying who outranks whom

You compare two things on a *dimension*:

```
ada is more suspicious than bo
cy is more suspicious than ada
dan is more suspicious than bo
```

Each line is one arrow: *cy → ada* on the suspicion dimension. Saying `bo is
less suspicious than ada` draws exactly the same arrow the other way round —
*more* and *less* are one relation read in two directions, not two different
facts.

Chains of arrows compose. Ask about the ends of a chain and the machine walks
it:

```
is cy more suspicious than bo   →  yes
is bo more suspicious than cy   →  no
```

The first answer is worked out, not stored: cy outranks ada, ada outranks bo,
so cy outranks bo. The second is its mirror — if the chain runs one way, the
strict opposite is a real *no*.

## The honest gap

Now the question the ordering *can't* answer:

```
is cy more suspicious than dan   →  unknown
```

Both outrank somebody, but no chain connects them — in either direction. The
machine reports exactly that. This *unknown* is not a shrug or a failure; it's
the correct description of a **partial order**. Rankings-by-comparison are full
of such gaps, and a reasoner that fills them in — by alphabet, by vibes, by
whoever was mentioned first — is manufacturing knowledge. The gap is the answer.

(Chapter 5's *no* was "nothing supports it, so — for now — no." This *unknown*
is different: it isn't that nothing supports a ranking, it's that the question
genuinely has no answer yet. New comparisons could settle it either way.)

## Rungs make strangers comparable

There's a second way to rank, and you've had it since the graded rules of
Chapter 4: put each thing on a *rung* with a word like `very` or `slightly`.

```
suspicious is gradable
fay is very suspicious
gil is slightly suspicious
```

Fay and gil have never been compared to anyone — no arrows at all. But they're
each on a rung, and rungs line up:

```
is fay more suspicious than gil   →  yes
is fay as suspicious as gil       →  no
```

This is the bridge between the two ways of grading. Arrows compare *pairs*;
rungs place *individuals*; and where both exist they meet — which is exactly why
the machine keeps the dimension (`suspicious`) visible in every comparison
instead of welding it into some one-off `more_suspicious` relation. One caution,
though: rungs are coarse. Two suspects on the *same* rung get an honest
`unknown` to the strict question — being equally *"very suspicious"* doesn't
rule out a finer difference between them.

## When the story contradicts itself

What if a witness swears the ranking runs in a circle?

```
ada is more suspicious than bo
bo is more suspicious than cy
cy is more suspicious than ada
```

A strict order can't loop — somewhere, someone misspoke. The machine doesn't
explode, and it doesn't silently pick a winner either. Its consistency check
simply points at the knot:

```
comparison cycle on 'suspicious': ada > bo > cy > ada
```

Same for a comparison that fights the rungs (declared *more suspicious* but
sitting on a *lower* rung): flagged, not detonated. Contradictions in testimony
are things a detective **investigates**, not things that end the investigation —
so they surface as warnings for you to resolve, and the rest of the world keeps
reasoning.

!!! note "Try it live"
    The [uncertain case](../playground/uncertain.md) playground has the whole
    kit in one world — suspicion rankings included. Ask it
    `is cy more suspicious than dan` and watch it decline, honestly.

---

**Next:** a puzzle every detective faces — when do two *names* refer to one
*person*? [Same name, same person? →](10-identity.md)

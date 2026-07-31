# Asking: yes, no, and *I don't know*

A world full of things isn't much use if you can't ask about it. This chapter is
the other half of the conversation.

It's also where the machine does something most software refuses to do: admit
ignorance, and be precise about what its ignorance means.

## A question is a wish that you're not going to act on

Look at how you ask:

```
ask is the salt sealed?:
    salt.sealed = true
```

Now look back at the goal from Chapter 0:

```
goal build a tower:
    a on b
```

**Same shape.** A word, a label, and a body of things that should be true. That
is not a coincidence in the notation — it's the machine's actual position:

> **A question is a goal.** *"Is the salt sealed?"* is the goal *find out whether
> the salt is sealed*, and answering it is pursuing it.

There's no separate question-answering engine here. The thing that searched for
a way to build a tower is the thing that searches for a way to establish that
the salt is sealed. Only the verb differs — `goal` means *go and make it so*,
`ask` means *tell me whether it could be so*.

## The answer comes with its reasons

The pantry knows one action: **seal** a jar. Nobody has sealed anything. Ask
anyway:

```
YES - derived in 1 step(s) (1 step(s) considered)
yes, because:
  seal(j=salt)
```

Yes — *and here is what would make it so*: seal the salt jar. The machine didn't
just check; it **worked out a way**, and the way is the answer's justification.

That's worth dwelling on. The explanation was not assembled afterwards by some
reporting layer looking back over a trace. Finding the answer and finding the
explanation were **the same act**, because what the machine searches for is
precisely a route from what it knows to what you asked. Chapter 8 is about
reading those routes as causes.

## Three answers, not two

Ask about something the machine has no way to establish — nothing in the pantry
has anything to do with being organic:

```
UNKNOWN - no derivation found - this says nothing about the world
```

**Unknown.** Not *no*. And read the second half of that line, because the
machine is being careful about something subtle: *this says nothing about the
world.* A search that came up empty has learned about **its own library**, not
about reality. The salt may well be organic; nobody here knows how to find out.

Now the third answer. This time the pepper is recorded as *not* sealed:

```
NO - refuted: pepper.sealed is already False, not True
```

That's a real **no** — not "I couldn't prove yes", but "I hold something
incompatible with yes". Two genuinely different situations, kept apart:

| | what happened | what it means |
|---|---|---|
| `yes` | found a route | it holds, or can be made to |
| `no` | found a contradiction | something incompatible is true *now* |
| `unknown` | found nothing | I have no way to settle this |

## Closing the world, on purpose

Sometimes "I couldn't find it" really *should* mean no. If your list of staff is
complete, then someone not on it doesn't work here. That assumption has a name —
**closing the world** — and the machine will make it, if you ask:

```
NO - nothing known makes it true, and the library is assumed complete
```

Same question, same world, different answer — and it says exactly which
assumption it leaned on. That's the point. Closing the world is a **stance**, a
thing you choose, not something baked into the machinery. The default is the
humble one.

!!! warning "This is the crack most reasoners fall through"
    The tempting shortcut is to treat "no derivation found" as *false*, because
    it makes the system look decisive. But a missing arrow isn't a denial: the
    graph not saying the salt is organic is not the graph saying it isn't. Once
    a system quietly converts ignorance into denial, every answer it gives is
    slightly untrustworthy and you can't tell which ones.

## Asking changes nothing

One last property, easy to miss and load-bearing. When the machine answered
*yes* by working out that sealing the salt would do it — **it did not seal the
salt**. The route was worked out in a private copy of the world.

So you can ask freely. Questions don't saturate the graph with everything the
machine happened to derive along the way, and asking twice doesn't compound.

If you *want* to keep what it worked out, you say so, and then the derivation is
replayed for real. Which sets up the question the next chapter answers: what
exactly *is* one of these steps that the machine can either imagine or run?

## It refuses what it can't read

Ask about a jar that isn't there:

```
refused: line 2: nothing here is called 'vinegar'
```

Not an empty answer, not a guess — a refusal, with a line number. The same
happens if two things answer to one name, because guessing between them would be
inventing what you meant. A machine that can't refuse can't be trusted to
understand.

---

**Next:** the thing at the centre of all this — a rule. It's not what you're
expecting. [A rule is a little program →](04-rules.md)

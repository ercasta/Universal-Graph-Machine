# Who said it, and taking it back

Everything you've told the machine so far, it has absorbed. You wrote a
preference in Chapter 17, a recipe in Chapter 18, and the machine built the
thing you described and got on with it.

And recorded nothing whatsoever about the fact that **somebody said so**.

That's a bigger hole than it sounds. The machine could hold what it had been
told and could not point at *the telling*. So it couldn't be corrected, couldn't
say where a rule came from, and couldn't cope with a second person in the room.

## An utterance is a thing in the world

The fix is one decision made in the right direction: saying something is an
event **in the world**, and the machine's own notes merely attend it.

Not the other way around. Chapter 13 was firm that the thread points at the
world and is never pointed at by it, and adding a third kind of entry to the
thread would have broken that. So the utterance hangs off the conversation, it
points at whatever it authored, and the thread notices it — same as it notices
anything else.

And the speaker is a **node**:

```
who said it : bob
```

The first version stored that as a piece of text — `by="user"` — which is this
project's own standing rule broken in a single line: *never identify anything by
name alone.* Harmless with one person in the conversation. Useless the moment
there are three, and impossible if you ever want to doubt someone, quote them,
or grant them standing.

## Taking something back

Once the telling is a thing, so is un-telling it.

```
bob    : prefer bob's way
boss   : (withdraws it)

the block is withdrawn  : True
the utterance survives  : True
speakers on the record  : ['bob', 'boss']
```

Three things happened there, and each is deliberate:

- **The outcome really changed.** The withdrawn advice is skipped by whatever
  enumerates advice, so the machine genuinely plans differently afterwards. This
  is not a cosmetic flag.
- **History survived.** The block is *marked*, not deleted, and the utterance is
  still sitting there. You can still ask what bob said and when.
- **The retraction is itself on the record**, said by somebody, at a point in
  the order.

Retracting nothing, or retracting the same thing twice, is refused. Both are
almost certainly a mistake, and quietly succeeding would hide it.

## Whether you *may* is a question about the world

Here's where having a second person changes the answer rather than just the
bookkeeping.

*"Ignore that"* is not a global fact once there are three speakers. It's an act
by somebody, and whether it lands is a question of **standing**. Before this,
anyone could withdraw anything — a policy nobody had chosen, which is the worst
kind.

So: a speaker may always withdraw their own words. Anything else has to be said,
out loud, in the world:

```
alice tries to withdraw bob's advice:

  'alice' cannot withdraw what 'bob' said. A speaker may withdraw their own
  utterance; anything else needs authority, which is world data.
```

Declare the authority and the same attempt succeeds:

```
boss outranks alice;  alice outranks bob

boss may withdraw bob's advice  : True     (transitively)
bob may withdraw the boss's     : False    (it has a direction)
bob may withdraw his own        : True     (always)
```

Transitive, because a supervisor over a lead over an agent is the case that
makes having a *relation* worth the trouble at all. Directional, because a
ranking that worked both ways wouldn't be one.

Keep an eye on what this **doesn't** do: the machine has no built-in idea of
organisations, roles, or seniority. It has one relation, declared by you, in the
same graph as everything else — so it can be inspected, argued with, and
changed. Chapter 31 is about to reuse it for something that looks completely
different.

## The machine can ask, too

A conversation that only runs one way isn't one. And notice that *confirming*
something with the machine is impossible unless it can ask — there has to be
something on the record for your answer to be an answer **to**.

```
system : which file did you mean?
user   : driver.py

asked by                : system
the reply answers it    : True
anything left pending?  : ()
```

This needed no new machinery at all. Asking is a trip through the **same door**
as every other outside action — it leaves the machine, comes back with
information, and is registered as *only looking*, since it costs time and
changes nothing. Which means a standing prohibition can veto asking, exactly
like anything else, through the one choke point.

People are not functions, though, so the realistic case is that nobody answers
right now. Because the question is committed to the record *before* the handler
runs, a host that fails or simply goes away still leaves a machine that can say
what it was waiting for:

```
the handler raises      : nobody is at the desk
still pending           : ['shall I commit?']

...an hour later, the reply arrives:
pending                 : ()
```

Answering later is the same recording as answering immediately. And answering
something that was never asked is refused.

## Hearing what somebody else wrote

Now the case this design was really for.

Suppose another piece of software writes into the graph — its own process, its
own locks, following the conventions for how a conversation is represented. That
makes the **conversation the integration surface**: you talk to this machine the
same way whether you're a person or a program.

Except the machine couldn't see any of it. Its record of what had been said was
read off its own notes — a record of *what it had attended to* — so an utterance
put there by anyone else was in the world and heard by nobody.

```
another process writes: "prefer theirs"

heard?                  : False
listed as unattended    : True
after attending         : heard, in conversation order
attending again         : ()   ← nothing new
```

Attending isn't a formality. It's what puts an outside utterance into the **one
order** everything else depends on — the same order that carries applications,
questions and retractions. *"Was this already acted on?"* is answerable only
because all of those share one sequence. An utterance that never joins it can
never be reasoned about in time.

The idempotence matters for a practical reason: a running loop will call this
every tick, and a version that re-attended everything each time would duplicate
the entire history within seconds.

---

**Next:** rules that hold — unless somebody with standing says otherwise.
[Overruled →](31-overruled.md)

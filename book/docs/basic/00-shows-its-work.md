# A machine that shows its work

Let's start with the smallest interesting thing this machine can do, and then
take it apart.

Here is a complete program. It is two lines.

```
rule <mortality> = implies( { +person($p), no mortal($p) }, { +mortal($p) } )

fact +person(paul)
```

Run it, and ask about Paul:

```
$ python -m ugm mortal.ugm --ask "mortal(paul)" --ask "mortal(sara)"
mortal.ugm: 2 ticks, ended quiescent

what it believes, newest first:
  mortal(paul)
  person(paul)

mortal(paul): believed

mortal(sara): not believed
```

Nobody wrote down that Paul is mortal. You asserted one fact, and the machine
worked the rest out on its own — and then told you honestly that it has never
heard of Sara at all.

## Read the belief list slowly

That short reply has more in it than it looks.

- **`mortal(paul)`** is in the list, and you never wrote it. Somewhere between
  loading the file and printing the answer, the rule fired and this became
  part of what the machine believes.
- **`person(paul)`** is in the list too — the one thing you actually asserted.
  Both lines are just *believed*. Nothing marks one as "given" and the other
  as "derived"; the machine keeps no such distinction once a belief lands.
  Chapter 2 is about why that's the *right* amount of bookkeeping, not a
  missing feature.
- **`mortal(sara)`** is not in the list, and asking about it says `not
  believed` — not *false*. Nobody has ever told this machine anything about
  Sara. Chapter 3 is about the difference between *nobody claims this* and
  *something denies this*, and why collapsing them is a mistake systems make
  all the time.

## Why the rule needed that extra clause

Look again at the antecedent: `+person($p), no mortal($p)`, not just
`+person($p)`.

Try it without the second clause and the run never finishes:

```
rule <mortality> = implies( { +person($p) }, { +mortal($p) } )
```

```
mortal.ugm: 400 ticks, ended applied
  stopped at the tick limit (400); it had not finished
```

Paul stays a person forever, so the rule matches forever — and this machine
does not quietly notice that applying it again would change nothing. **An
application that writes nothing is still offered again next tick**, because
deciding a rule has nothing further to give is the corpus's judgement, not the
engine's. A rule stops itself, by asking for the absence of what it's about to
conclude. `no mortal($p)` is that stop.

You'll see this shape everywhere from here on: a rule that concludes something
permanent usually needs to ask, first, that the conclusion isn't already
there.

## Two ticks

The run said `2 ticks, ended quiescent`. A tick is one move: the machine
scored every rule, took the one whose antecedent matched, applied it, and
wrote down what followed. It stopped when nothing left to try would change
anything — which is what *quiescent* means, and which is itself a fact
deposited about the run rather than a state hidden in an interpreter.

There is no compile step, no phase order, no "inference engine" with a fixed
pipeline inside it. There is one loop, and everything that happens on it —
believing what a channel told you, deriving a fact, deciding you're done —
happens because some rule was selected and applied.

## What this book is going to do

Roughly, it will strip away layers.

Part 1 shows you the memory: what a claim looks like, and how *is this true?*
gets answered.

Parts 2 to 5 show you what you can teach it: rules, goals, uncertainty, time,
other people.

Parts 6 to 8 turn the machine around to look at itself: its own commitments as
ordinary facts, the things that genuinely could not be taught, and how
something made of rules manages to read its first rule at all.

!!! note "Deep dive: what happened to *why*"
    An earlier version of this engine answered a second question after every
    run — `--why mortal(paul)` — and walked back a proof: which rule, which
    premises, all the way to what you'd typed. That machinery is gone. It
    depended on every claim carrying a licence and a place in a history, and
    both went when the history did (Chapters 4 and 5 tell that story in full).
    What's left is honest about the trade: `python -m ugm` prints the whole of
    what's believed, and nothing is hidden behind a summary — but there is no
    programmatic explanation trail either, in this repo, right now. It's listed
    as a real gap, not a secret, in Chapter 34.

---

**Next:** before we can talk about claims, we need to see what everything here
is built out of — and it's shorter than you'd expect.
[Nodes, members, and nothing else →](01-the-substrate.md)

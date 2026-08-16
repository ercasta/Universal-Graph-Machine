# A proposition claims nothing

`on(a, b)` is a node with two members. It is the *idea* that a is on b.

It is not the assertion that a is on b.

That distinction looks like philosophy and is in fact forced, by a very short
argument. Suppose you wanted to say *`on(a, b)` is false*. To say that, you have
to be able to **point at** `on(a, b)` — which means the node has to exist. But
if building the node were itself the act of asserting it, then creating a
proposition in order to deny it would assert it first.

> **Two levels are what negation costs.**

So the claim is a separate node, called an **entry**:

```
<e> = entry( <M7>, on(a, b), + )
```

Three members, and never a fourth:

| member | what it is |
|---|---|
| **locus** | the moment (or stretch of time) the claim is *about* |
| **proposition** | what is claimed |
| **sign** | how it is claimed — `+`, `−`, or `?` (Chapter 3) |

In exchange for the extra hop, nothing in the system ever has to *remember* that
a bare proposition means nothing. It structurally cannot be mistaken for a
claim, because it has no locus and no sign.

## What the two levels buy

Here is the payoff, and it is the reason to care.

Two very different things happen in the world, and a system with one level
cannot tell them apart:

| | what happened | how it's written |
|---|---|---|
| they stopped being on each other | **the world moved** | a **new entry**: opposite sign, later locus |
| I was mistaken that they ever were | **my record was wrong** | a **fact about the old entry**; the entry is untouched |

If truth were a value stored on the proposition node, both of those would be
"change it", and a system that cannot distinguish them quietly rewrites its own
history. Here the first adds a claim and the second adds a claim *about a
claim* — and both remain readable afterwards.

```
mistaken(<e>)              my record was wrong
outranks(<e1>, <e2>)       Anna's claim beats Bo's
supposed(<e>, <S>)         I believe this only inside supposition S
```

Those are ordinary propositions that happen to have entry nodes as members.

## Where the regress stops

An entry is itself a fact. Doesn't it need an entry of its own? And that one
another?

No, and the reason is structural rather than a convention someone has to
remember:

> **An entry names its locus, so it is located by being one.**

A proposition needs an entry in order to be placed somewhere. An entry places
itself. The recursion terminates at depth one, by construction.

The claim is narrow, and the narrowness is what makes it hold. An entry needs no
entry **to be located**. It may freely be the *subject* of another entry's
proposition — that's the three lines above. Locus and member are different
relations to an entry, and only the first one would regress.

## Two coordinates in time, and only one is a member

This is the subtle one, and the whole of Chapter 5 depends on it.

An entry has a **locus** — what the claim is about — and it also sits in some
particular moment's list of changes. That second thing is its **deposit
moment**: *believed since here*.

```
<M12> = moment( delta:       <e1>, <e2>, <e3>
                predecessor: <M11>
                licence:     <application-of-R1> )
```

The delta membership is already structure. It costs nothing and cannot be
omitted. So an entry has two temporal coordinates and stores exactly one of them
as a member; the other is simply *where it sits*.

Keeping them apart is what lets the machine revise its view of the past without
rewriting it. An entry deposited in `M12` may have `M7` as its locus — *I now
think it was raining then* — and that is the ordinary form of learning something
about the past, not a special mechanism.

Conflate them and every claim would be forced to be about the moment it occurred
to somebody.

## Everything else is an ordinary fact about the entry

```
licensed_by(<e>, <application>)     said_by(<e>, anna)     at(<e>, 09:14)
```

Not members. Facts. This matters for a reason that is easy to state and easy to
get wrong: a fact the machine *knows* but no rule can *ask about* is a defect.
It means the machinery acted on a judgement nothing can argue with.

That defect has been shipped in this design repeatedly, and the fix has been the
same every time — take the thing out of a hidden field and deposit it as a
record. Chapter 25 is where that becomes a working method rather than an
anecdote.

## Two claims about the same thing are two claims

Propositions have one identity however many times you build them: write
`on(a, b)` twice and you get the same node both times. That's why reference is
cheap here.

**Entries do not work that way.** An entry is an *act of claiming*, so two
claims about the same proposition at the same locus are two different nodes.
Otherwise `mistaken(<e>)` would land on both the mistake and its correction at
once.

The same holds one level up: two rules that happen to say the same thing are
still two rules, with different authors, provenance and standing.

!!! note "Deep dive: contradiction is allowed, and nobody checks"
    Two entries in one locus with opposite signs is a shape the substrate
    permits. This is deliberate. Consistency is **a question you ask**, not an
    invariant the substrate maintains — the alternative is checking every write
    against every other claim in memory.

    The honest consequence: *is this moment consistent?* is a query somebody has
    to actually run. And there is currently no vocabulary for saying that two
    propositions are *incompatible* — you can deny one, but you cannot say they
    cannot both hold. Chapter 34 lists that as a real gap.

## Variables belong to the statement that wrote them

One more rule, small-looking and load-bearing.

`?x` in one line you write and `?x` in the next line are **different nodes**.
A statement's variables belong to it.

This is what makes a rule a self-contained claim rather than a fragment of a
global namespace, and it is a wall you will hit if you try to write a guard for
one rule inside a different statement. Chapter 17 shows the exact trap; the fix
is always to put the variable where the rule's own variables live.

> **Reference is binding.** Anything deposited as an entry can be bound by a
> rule's antecedent, and that is how a plan, a hypothesis, a rule or a
> prohibition is referred to. Names are for the exceptions.

---

**Next:** the third member of an entry, which has three values and a fourth
possibility that isn't a value at all.
[Three signs, and silence →](03-signs.md)

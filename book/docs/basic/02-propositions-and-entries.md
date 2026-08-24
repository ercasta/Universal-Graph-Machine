# A proposition claims nothing

`on(a, b)` is a node with two members. It is the *idea* that a is on b.

It is not the assertion that a is on b.

That distinction looks like philosophy and is in fact forced, by a very short
argument. Suppose you wanted to say *`on(a, b)` is false*. To say that, you have
to be able to **point at** `on(a, b)` — which means the node has to exist. But
if building the node were itself the act of asserting it, then creating a
proposition in order to deny it would assert it first.

> **Two levels are what negation costs.**

So the claim is a separate node, called an **anchor**:

```
believed(on(a, b))
```

One member, and never a second: the proposition. Presence of this node is
what "believing something" means here, and it is the whole of what it means.
There is no field on it for how strongly, no field for who said so, no field
for when.

```
on(a, b)                 structure. Never believed on its own.
believed(on(a, b))       present = believed. Absent = not.
```

In exchange for that extra hop, nothing in the system ever has to *remember*
that a bare proposition means nothing. It structurally cannot be mistaken for
a claim, because nothing points at it as believed.

What a claim says, it says by an **act**: asserting mints this node, erasing
deletes it. There is nothing stored on the anchor beyond its presence —
Chapter 3 is the full account of what that buys.

## Asserting twice is not two things

Believing is a set membership test, and the anchor is **interned** — the same
proposition always gets the same anchor. Assert it twice and nothing doubles:

```
fact +poisoned(a)
fact +poisoned(a)
```

```
what it believes, newest first:
  poisoned(a)
```

One line, not two. There was nowhere for the second assertion to go: it asked
whether `poisoned(a)` was believed, found that it already was, and had nothing
left to do. This is not a deduplication step bolted on afterwards — it falls
straight out of interning, the same mechanism that makes `on(a, b)` one node
however many times a rule mentions it.

It matters practically, too: a rule whose consequent restates something
already true does not create a second act of claiming it. Chapter 0 already
leaned on the flip side of this — a rule that could *keep* matching has to be
the one that stops itself, because the machine will not decide on your behalf
that reapplying it would be pointless.

## What erasing costs

Believe `poisoned(a)`, then erase it — the anchor is *deleted*, not
superseded. Nothing about the earlier belief survives the erasure
automatically:

```
rule <cure> = implies( { +healed($x), +poisoned($x) }, { -poisoned($x) } )

fact +poisoned(a)
fact +healed(a)
```

```
poisoned(a): not believed
```

If a corpus wants to remember *that* it changed its mind, and not just the new
state, that has to be written down on purpose — an ordinary fact deposited
alongside the erasure, `{-poisoned($x), +cured($x)}`, not something the
substrate hands you for free. **Never considered** and **considered and
retracted** are, by default, the same state: absence. That is honest — nothing
here remembers on your behalf.

## Where the regress stops

A proposition needs an anchor in order to be believed at all. Doesn't the
anchor need one too? And that one another?

No, and the reason is structural rather than a convention someone has to
remember: the anchor relation, `believed`, is never itself wrapped in another
`believed(...)`. Asserting is the one act that reaches into the graph and
mints this node; nothing asks *is this belief believed* recursively, because
there is nothing beyond presence for a second layer to add.

An anchor may still freely be the *subject* of some other fact, while it
exists — `mistaken(<that anchor>)`, `said_by(<that anchor>, anna)` — the same
way any node can be. But once it's erased, it's gone, and a fact still naming
it points at nothing: reading a deleted node's structure answers rather than
raises, but there is no relation left to match against it. Say what you need
to say about a claim *before* you take it back.

## Everything else is an ordinary fact about the anchor

```
licensed_by(<a>, <application>)     said_by(<a>, anna)     doubted(<a>)
```

Not members. Facts, written the same way any other proposition is. This
matters for a reason that is easy to state and easy to get wrong: a fact the
machine *knows* but no rule can *ask about* is a defect. It means the
machinery acted on a judgement nothing can argue with.

That defect has been shipped in this design repeatedly, and the fix has been
the same every time — take the thing out of a hidden field and deposit it as a
record, something a corpus can write about an anchor while it still exists.

## Two rules that say the same thing are still two rules

Propositions have one identity however many times you build them: write
`on(a, b)` twice and you get the same node both times, and an anchor for it
interns the same way. **Rules do not work that way.** A rule is an authored
statement, not an idea — two rules that happen to conclude the same thing are
still two different nodes, with different authors, provenance and standing.
`dormant(<R1>)` never accidentally reaches `<R2>` because the two look alike.

## Variables belong to the statement that wrote them

One more rule, small-looking and load-bearing.

`$x` in one line you write and `$x` in the next line are **different nodes**.
A statement's variables belong to it.

This is what makes a rule a self-contained claim rather than a fragment of a
global namespace, and it is a wall you will hit if you try to write a guard for
one rule inside a different statement. Chapter 17 shows the exact trap; the fix
is always to put the variable where the rule's own variables live.

> **Reference is binding.** Anything believed can be bound by a rule's
> antecedent, and that is how a plan, a hypothesis, a rule or a prohibition is
> referred to. Names are for the exceptions.

!!! note "Deep dive: contradiction is allowed, and nobody checks"
    A proposition and its own denial can both be believed at once, and the
    substrate does nothing to stop it:

    ```
    fact +poisoned(a)
    fact +not(poisoned(a))
    ```

    ```
    poisoned(a): believed
    not(poisoned(a)): believed
    ```

    This is deliberate. Consistency is **a question you ask**, not an
    invariant the substrate maintains — the alternative is checking every
    write against every other claim in memory.

    The honest consequence: *is this believed thing consistent?* is a query
    somebody has to actually run. And there is currently no vocabulary for
    saying that two propositions are *incompatible* — you can deny one, but
    you cannot say they cannot both hold. Chapter 34 lists that as a real gap.

---

**Next:** the two ways a rule can look at absence.
[Three signs, and silence →](03-signs.md)

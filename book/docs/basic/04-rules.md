# A rule is a little program you point at

So far the machine only knows what we hand it, plus whatever shapes those things
happen to satisfy. This chapter adds the thing that turns a filing cabinet into
something that reasons: **rules**.

But the machine's idea of a rule is probably not the one you're carrying, and
the difference is the single most important idea in this book. So let's start
with what a rule is **not**.

## The usual idea, and why it isn't this one

In most reasoning systems, a rule looks like this:

```
    a jar is sealed   when   someone puts a lid on it
```

and it works by **firing**. You drop a fact into the system, the system finds
every rule whose left-hand side matches, and those rules go off — adding facts,
which match more rules, which go off too, until nothing new happens.

It's a lovely idea and it has a hard problem at the centre. **Nothing is
pointed at anything.** A rule fires wherever the world happens to match, so as
your rulebook grows you stop being able to predict what will happen when you add
a fact. You start writing rules whose job is to stop other rules. You add
markers meaning "already done" so things don't fire forever — and forgetting one
produces an endless stream of effects with no obvious culprit.

This machine doesn't do that. Here:

> **A rule is a function. It has parameters. It runs when something calls it,
> on the arguments it's given, and never otherwise.**

## What one looks like

Here's the whole of a rule, exactly as the machine stores it — this is its own
output, read back out of the graph:

```
# Put the lid on a jar.
fn seal(j: jar) -> sealed_jar:
    SET F(j) "sealed" true
```

Four lines, and three of them are about the outside:

- **`fn seal`** — its name.
- **`(j: jar)`** — it takes one argument, called `j`, and that argument must be
  a jar. Remember Chapter 2: *jar* is a shape, so this is checked by looking at
  the thing, not by trusting a label.
- **`-> sealed_jar`** — when it's done, its argument will satisfy the shape
  *sealed jar*.
- **`SET F(j) "sealed" true`** — the body. Put the lid on.

The comment isn't decoration either. It's stored *in the graph* alongside the
instructions, because a note that lives only in a text file is invisible to the
running system.

!!! note "Why does the body look like assembly?"
    Because it's honest, and because it's early. A friendlier surface will
    compile to exactly this, and nothing is wasted when it does. Assembly has
    one virtue worth a lot right now: it's unambiguous, so a translation from
    English is either right or *loudly* wrong, with no interpretive layer to
    hide a mistake in. Read `SET F(j) "sealed" true` as *"set the thing I was
    handed as `j` to sealed"* and you have it.

## Notice what the rule doesn't say

Read it again and look for the condition. **There isn't one.**

There's no `when`. Nothing in `seal` describes the circumstances under which
sealing should happen. That information isn't missing — it was never this
rule's business. The circumstances are decided by whoever calls it.

That's the trade at the heart of the design. A rule gives up the power to decide
when it runs, and in exchange it becomes something you can reason *about*: it
can't surprise you, it can't fire twice, and it can't interact with a rule
written by someone else who never heard of it.

## Pointing it at something

We have two jars, salt and pepper. Neither is sealed:

```
before             : salt None | pepper None
```

Now point `seal` at the salt:

```
after seal(j=salt) : salt True | pepper None
```

**The pepper is untouched.** That's the whole chapter in one line.

In a firing system, a rule about jars is a rule about *all* jars, and keeping it
off the pepper means writing a condition to exclude it. Here the pepper was
never in question, because nobody pointed at it. Wrong firing isn't unlikely —
it's structurally impossible.

And by Chapter 2's logic, the salt is now a different kind of thing:

```
is it a sealed_jar now? True | pepper: False
```

Nothing recorded that a sealing happened. The lid is on, so the jar satisfies
the shape. That's what "changing a type is changing a shape" buys.

## The rule is data, and that changes everything

Here's the part that pays off for the rest of the book. That rule isn't code
sitting in a file — it's nodes and edges in the same graph as the jars. Which
means the machine can **read it**.

Watch it work out what `seal` does, by looking at the instructions:

```
effects read off the body: [('attr', 'sealed', 'j', None)]
```

*Setting the attribute `sealed`, on whatever gets passed as `j`.* Nobody
declared that. No one wrote an "effects" section that could drift out of date
with the body — it **is** the body, read at the moment of asking.

This is how the machine planned the tower in Chapter 0. Faced with a goal it
can't yet satisfy, it asks each rule *could you make this true?* and reads the
answer off the rule's own instructions. That's what let it consider only three
possibilities instead of fifty-five.

!!! note "Deep dive: a rule that writes a rule"
    Because a rule is ordinary data, a rule can build another rule and store it.
    That isn't a party trick reserved for a test suite — it's how the machine
    learns in Chapter 14, turning a sequence of things it did into a new
    named rule it can call later. Nothing special is needed. Writing a rule is
    writing nodes and edges, and every rule can already do that.

## What you give up, and what you get

Being honest about the cost: **nothing happens on its own any more.** In a
firing system, adding a fact sets off a cascade and you get consequences for
free. Here, if nobody calls anything, nothing runs. The machine needs something
to *decide* — and that decision is now the whole game.

Which is exactly where Part 2 begins. The machine decides by wanting something.

---

**Next:** goals — how you tell it what you want, and why "what must be true" beats
"what to do". [Wanting something →](../intermediate/05-wanting-something.md)

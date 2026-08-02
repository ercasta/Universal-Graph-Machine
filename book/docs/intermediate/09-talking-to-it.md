# Talking to it

You've been speaking this language since Chapter 0 without anyone explaining it.
That was on purpose — it's meant to be readable before it's taught. This chapter
makes it explicit, and then makes the case for why it's so deliberately small.

## Three verbs, one grammar

```
goal build a tower:        ask is it built?:        why is it built?:
    a on b                     a on b                   a on b
    b on c                     b on c                   b on c
```

Look at what changed between them. **The verb. Nothing else.**

That's not the parser being economical. It's Chapter 3's claim showing through
in the notation: a question *is* a goal. The constraints are identical, the node
the machine builds is identical, and what differs is only what it then does —
pursue it, answer it, or explain it.

So the machine records which verb you used, because that genuinely *is* extra
information. You can't recover it from the constraints: wanting something,
doubting it, and asking how it came about are three different acts about the
same proposition.

## And the whole vocabulary

Everything you can say:

```
a on b                  a relationship between two named things
b.clear = true          an attribute with a value
box.contents known      go and find out — rather than make it so
some file               something of this kind must exist
a is a sealed_jar       this thing must satisfy this shape

never unstack           don't use that action
never touch c           leave that thing alone
must paint              include this somewhere
at most 3 steps         a budget
```

Nine forms. That's the entire language.

The third one is the odd one, and it's worth reading twice. `box.contents =
"a spanner"` says *make it so*. `box.contents known` says *go and look*. Those
are different requests, and Chapter 19 is about why the machine couldn't tell
them apart until recently.

## Four more verbs, and the same block

`goal`, `ask` and `why` are three of seven. The others turn up in Part 4:
`prefer` and `avoid` write a guideline, `method` and `procedure` write a
decomposition. Same `verb label:` block, same indented body, same refusals.

That mattered more than it looks. For a while, a goal could be *said* while a
guideline could only be built by calling into the machine's own code — which is
precisely the "reach past the surface" the box at the end of this chapter says
must never happen. The principle was written down and quietly unenforced, for
everything except goals.

## Constraints on the route work in questions too

Here's something that falls out for free and is genuinely useful. Those bottom
four forms aren't goal-only. Paul is a person, and one rule concludes that
people are mortal. Ask whether he's mortal *without using that rule*:

```
ask without that rule?:
    paul.mortal = true
    never conclude_mortal
```

```
UNKNOWN - no derivation found - this says nothing about the world (0 step(s) considered)
```

Without the ban, the same question answers `YES` in one step. And `at most 2
steps` asks *"is this derivable in two steps?"* Nothing was added to support any
of this — constraining the route is constraining the route, whether the route is
a plan of action or a chain of reasoning.

!!! warning "A limit worth knowing: a mistyped action name is silently accepted"
    `never conclude_mortl` — note the typo — parses happily and forbids
    nothing, because it names no action the machine has. You'd get `YES` and
    reasonably believe you'd ruled something out. Unlike a mistyped *thing*
    name, which is refused on the spot, a mistyped *action* name currently
    passes. Worth knowing until it's fixed.

## Why it's this small

The honest history matters here. Earlier versions of this project tried to
translate ordinary prose into arbitrary graph structure. The measured result was
**0 out of 50** on real prose, and the gap was diagnosed as almost entirely
about grammatical construction rather than vocabulary.

That failure wasn't surprising in hindsight, because the target was unbounded.
Translating English into *anything* is a research programme.

What changed isn't the parser. It's the **target**. Once a goal became a handful
of constraint nodes from a closed vocabulary, translating into eight forms
became an ordinary problem. The intake got tractable because the thing being
built got small — not because anyone got cleverer about language.

## Refusing is the feature

This language can say no, three ways, all loud.

**A line it doesn't recognise.** The vocabulary is closed, so an unfamiliar
sentence isn't handled on a best-effort basis — it's refused with a line number
and the list of forms.

**A name that matches nothing:**

```
refused: line 2: nothing here is called 'vinegar'
```

**A name that matches more than one thing.** Remember Chapter 1: a label is a
sticky note, not an identity. If two things answer to "the salt", the machine
refuses rather than picking. Choosing would be inventing what you meant.

And when it refuses, **nothing is left behind**. Not a partial goal, not half a
question. A half-built goal is worse than none, because the machine would go and
pursue it and appear to be working.

!!! note "Where a language model fits"
    A model may **write this text**. What it must never do is reach past the
    surface and build graph structure directly — because then nothing could
    refuse it, and the refusals above are the entire safety property. The model
    proposes a sentence in a closed language; the machine accepts or rejects it
    deterministically. Same arrangement as Chapter 4's rules, which have their
    own text surface for exactly the same reason.

## Reading it back

The machine can render any goal or question back into the language it came from:

```
ask is paul mortal?:
    paul.mortal = True
```

That round trip is what lets a writer — human or model — check what the machine
actually understood, rather than what they hoped they'd said.

!!! note "Everything here is you talking *to* it"
    The machine can also **ask you** something, and it records both directions
    the same way: who said what, in one order, retractable. That's
    [Chapter 30](../world/30-who-said-it.md) — and it's what makes it possible
    to *correct* the machine rather than only to instruct it.

---

That's Part 2. The machine can want things, imagine them, find routes, explain
itself, and be spoken to. Everything so far has assumed the world cooperates.

**Next:** it doesn't. [When reality disagrees →](../advanced/10-when-reality-disagrees.md)

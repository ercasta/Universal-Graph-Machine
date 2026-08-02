# Not knowing

There's a box on the shelf. What's in it?

Up to this chapter the machine had no way to hold that question. An attribute
was either present or absent, and absent meant *hasn't got one*. So "the box has
no contents" and "nobody has looked in the box" were the same fact, which is to
say the second one didn't exist.

Chapter 3 made a great deal of the difference between *no* and *I don't know*
when the machine answers you. This chapter is that same distinction pointed at
the world instead of at the answer — and it took much longer to arrive.

## What was actually wrong

The machine could already do information-gathering. It has an action that scans
a directory. But look at how that action had to be described: its stand-in
version **creates file nodes**, as though scanning a folder brought the files
into existence.

That fudge worked, and it's why planning toward "some file exists" succeeded
back in Chapter 7. But it meant the machine could not tell these two apart:

- *make `p` true*
- *find out whether `p`*

And underneath that, one more thing was broken in a way that's easy to miss:
when a search failed, the machine reported failure identically whether **no
plan exists** or **no plan exists given what I currently know**. Only the second
of those is a reason to go and look.

## A value that means "not looked"

The fix is one sentinel. A slot can now hold `UNKNOWN`, which is neither a value
nor an absence:

```
attr: UNKNOWN   |  truthy: False
```

It's there — the slot is not empty — and it isn't a value either. Anything that
tests it gets `False`, so nothing accidentally concludes something from it.

And there's a matching thing you can say in a goal:

```
goal find out what is in the box:
    box.contents known
```

Read it out loud and the difference from every other goal in this book is
audible. `box.contents = "a spanner"` is *make it so*. `box.contents known` is
*go and look*. The machine renders it back to you as:

```
box.contents must be known
```

## Two reasons a goal isn't done

Chapter 5's goal keeps its conditions separate so the machine can ask *which
ones are still false*. That's what makes means–ends planning possible at all.

This chapter extends it by exactly one notch. A condition that isn't satisfied
is now unsatisfied for one of **two** reasons:

| why it's unmet | what to do about it |
|---|---|
| it's **false** | find an action that makes it true — everything so far |
| it's **unknown** | find an action that would *reveal* it — `sense` |

```
unmet: 1   undetermined: 1   blocked_on_ignorance: True
```

No new planner was needed for this. The machine already reads off each action's
own body what that action writes (Chapter 22), so it can already tell you which
actions would fill in a given slot. All that was missing was a second reason for
a condition to be open.

Give it an action that looks in the box, and the goal closes the honest way:

```
carried out: True   |  contents now: a spanner
```

Only after the action really ran. Imagining looking in the box tells you
nothing, which is the whole point.

## Bottoming out, not touching

Here's the rule that keeps this from making the machine useless:

> Go and look only when the plan **bottoms out** in ignorance — when everything
> still open is open because nobody has looked.

Compare a goal with one unknown slot *and* some ordinary unfinished work:

```
mixed goal blocked? False
```

That goal touches ignorance, but it isn't stuck on it. There's real work to do
first. A machine that sensed on a mere touch would go and open every box it
could reach before doing anything useful, which is a recognisable failure mode
in people too.

!!! warning "Ignorance has to be declared"
    Absence still means *hasn't got one*. A slot is unknown only when something
    explicitly says so.

    The tempting generalisation — treat every absent attribute as unknown —
    would make the entire graph unknown, every condition undecidable, and every
    question unanswerable. It would also be **untrue**: most absences really are
    knowledge. The shelf has no owner because it hasn't got one, not because
    nobody checked.

!!! note "One thing this can't express, recorded rather than papered over"
    Only attribute slots can be marked unknown. A *missing link* has nowhere to
    put the marker — there's no slot to write on, because the thing that would
    carry it is the edge that isn't there.

    So *"I don't know whether `a` is on `b`"* has no representation, while *"I
    don't know what colour `a` is"* does. That's a real limitation of the
    substrate, and writing it down beats inventing a workaround that hides it.

## Breaking off to actually go and look

Knowing you're stuck is one thing. Doing something about it, halfway through a
plan, is another — and it's the thing the outer loop of Chapter 25 was really
wanted for.

Here's a world built to make the point sharply. The machine has one action,
`scan_dir`, whose entire effect is behind the door to the outside. Read its body
and you learn nothing:

```
what scan_dir establishes : nothing readable
```

So the ordinary guidance — *which action would close an open part of my goal?*
— is **structurally blind** to it. `scan_dir` can never be proposed as a step
toward anything, because as far as the machine can tell it does nothing. Ask it
to plan "know how many files are in `src`" and planning fails, every time.

Now give the same goal to the loop instead of the planner:

```
verbs taken : imagine, imagine, …, look, imagine, …
sensed      : ('scan_dir',)
src.count   : 3
goal        : MET
```

What happened between the two runs of `imagine` is the whole point. The search
ran out of ideas, the machine asked *why* — and the answer wasn't "there's no
route", it was "I can't plan this until I go and look". So it **stopped
planning and performed a real action**, and then carried on.

Three details are load-bearing.

**A failed search now has three outcomes, not two.** *No route exists* is
defeat. *No route exists given what I know* is a reason to go and look. Reading
both as failure is what kept this from working for so long.

**Sensing picks differently.** Since the usual "what would this close?"
reasoning is blind here, the machine can't use it. It picks directly: an action
that applies to what I'm looking at, whose body reaches the outside through
something registered as *only looking*.

**It replans rather than resuming.** The half-built search is thrown away, not
continued. That's deliberate and it costs something: what the machine just
learned might invalidate the whole plan, so a frontier assembled in ignorance is
worse than no frontier at all. You can see it in the record — two searches, not
one.

!!! note "The tick has to admit what it's about to do"
    Chapter 25 made a point of every tick announcing its verb *before* taking
    the step, so a caller can stop before anything irreversible. The first
    version of sensing reported `imagine` — while performing a real dispatch to
    the outside world. It reports `look` now. A tick that lies about its verb
    defeats the entire point of having one.

## When to assume and when to go and look

The machine assumes things constantly. Every imagined step substitutes a
stand-in for an action's real outcome — that's what makes planning cheap
(Chapter 6), and Chapter 10 is about what happens when reality disagrees.

So when is assuming fine, and when should it stop and find out? There's a
structural answer, and it's better than a judgement call:

> **The cost of a wrong assumption is bounded by what you'll have done before
> you discover it.**

If everything downstream of the assumption is still imagining, being wrong costs
nothing at all — execution diverges, the machine replans, no harm done. If
there's a real action downstream, being wrong costs a real and possibly
irreversible act.

And that's checkable rather than felt, because of Chapter 12's second limit:
every effect that reaches the world leaves through **one door**. You can look at
a plan and see whether that door is downstream of the assumption.

> Assume freely before the first irreversible act. Go and look where an
> assumption is holding one up.

!!! note "Deep dive: two bugs, neither caught by the tests passing"
    The first version of `known` stored the subject as a piece of text instead
    of a link to the thing. So the condition looked at nothing, found nothing
    wrong with nothing, and **closed itself before anyone had looked**. What
    caught it was rendering the goal back out as text — it came back as
    "something.colour" — which is the round trip earning its keep.

    The second was in the test. The contrast cases were evaluated *after* the
    action had already run, by which point the slot was known and every
    assertion passed no matter what the code did. A deliberately planted bug
    proved the test was checking nothing.

    Both of these are the same species: a check that passes for a reason
    unrelated to the thing it's supposed to be checking. If there's one habit
    worth taking from this book, it's asking what your passing test would still
    pass if the feature were deleted.

---

That's Part 4. You can now tell this machine what you'd prefer, what the
approved way is, what it may not work around, and what it should go and find
out — and every one of those is ordinary data it can be asked about afterwards.

**Next, and optional:** how the pieces actually work.
[The instruction set →](../deep/20-instruction-set.md)

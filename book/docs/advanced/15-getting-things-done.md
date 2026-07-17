# Getting things done

Everything so far has been about *knowing*. You tell the machine facts, it works
out consequences, and when you ask, it answers — carefully, and with its reasons.
A splendid clerk. But a clerk who only ever *answers* is only half of what an
agent needs to be. The other half is **doing**: taking a goal, following a
sequence of steps toward it, and coping when the world doesn't go to plan.

This chapter is about that other half. And the pleasing part — the part that keeps
faith with everything you've read — is that *doing* turns out to be more *knowing*.
The machine doesn't grow a new organ to act. It reasons about acting with the same
rules-and-facts it uses for everything else.

## A procedure is something you teach once

Here is a small routine, taught to the machine in one line:

```
to brew : add_beans then heat
```

Read it aloud and it's just English: *to brew, add beans then heat.* And that's
all it is to the machine, too — not a script, not a special "procedure object",
but a couple of **facts**. `brew` has two steps; one comes before the other. You
could have written those facts out longhand; `to … then …` is simply the
comfortable way to say them.

Now you can run it by name:

```
run brew
```

> *add_beans, then heat.* — the machine performs the two steps, in that order.

The order isn't magic, and it isn't hard-wired. The `then` you wrote became a fact
that one step comes before the other; running the procedure hands that ordering to
the same planner the machine uses for everything else, and the planner simply
won't let the second step go until the first is finished. Sequencing falls out of
ordinary reasoning — you'll see exactly where in a moment.

## Who actually *does* the step?

A fair question, because it cuts to the heart of what this machine is. When `heat`
comes up, something has to, you know, *heat things* — and that is emphatically not
the reasoner's job. The machine's job ends at the **decision**: it works out that
the next action is *heat*, packages that as a request — a name and its arguments —
and hands it **out** to you, the surrounding program, to carry out. You do the
heating (or the HTTP call, or the file write, or the asking-a-human); you hand back
what happened; and the machine folds that result into its facts and reasons on.

This is the line the whole design is drawn around. The reasoner decides; the world
is someone else's department. Everything with a side-effect, a delay, or a chance
of failure lives on your side of that line. The machine stays a pure, testable
reasoner that has never heard of the network — and *"the next action is heat"* is
just another fact it worked out, as inspectable as any other.

So a "procedure" is a plan the machine *carries* and the world *executes*, meeting
at that clean seam. Which raises the interesting question: what happens when the
plan the machine carries isn't quite complete — or when the world, having done its
part, doesn't deliver?

## When a step needs something nobody set up

Teach it a slightly richer routine. Heating needs water, and one of your steps
produces coffee only if there's water to heat:

```
to brew : add_beans then heat
```

…but suppose `heat` **requires water**, and nothing in your setup has put any water
out. A brittle system would march up to `heat`, find no water, and either crash or
quietly produce nothing. Watch what this one does instead:

> *add_beans, **get_water**, then heat.*

It slipped in a step you never wrote. Finding that `heat` needed water and that
nothing was providing it, the machine treated the gap as a small **problem to
plan** — and it happens to *have* a planner. It found something that produces water
(`get_water`), committed to it, and — because a producer must come before its
consumer — slotted it in *ahead* of `heat`. Your hand-written steps and the
machine's invented step run through **one and the same** gate; you can't tell, from
the outside, which was pre-arranged and which was figured out on the spot.

This is the first sense in which the machine "copes": a plan with a hole in it
isn't a dead end, it's a smaller planning problem. You supplied the shape of the
routine; the machine filled a gap you'd left.

## When the world doesn't deliver

Now the sharper kind of coping — the one every real agent needs and most handle
badly. A step runs. You carry out the action, hand back a result… and the effect
just *isn't there*. The heater clicked on but the mug is still cold. The API
returned 200 but the record didn't save. The action *happened* and yet it didn't
*achieve* anything.

A machine that trusts its plan will sail right past this. It marked the step done,
so as far as it's concerned the goal is met — and it will cheerfully report
success over a cold mug. That's the acting equivalent of the confident lie you met
back in [Chapter 5](../intermediate/05-no-and-unknown.md): mistaking *"I did the step"*
for *"the step worked."*

This machine checks. After a step finishes, it looks at what the step was *supposed*
to bring about and asks whether the world actually shows it. When the answer is no,
it records a plain fact — a **discrepancy** — and, crucially, that fact is not an
alarm bell or an exception hurtling up a stack. It's just data, sitting in the
graph, that other rules can react to. And the built-in reaction is exactly the one
you'd want: *don't retry the thing that just failed — find another way.* If there's
another route to the same effect, the machine takes it:

> *warm* — *(the mug stays cold; the effect never appeared)* — *…so:* **microwave.**

It tried `warm`, noticed the coffee never got hot, set that failed approach aside,
and reached for an alternative that produces the same result. No crash, no false
success — the failure became a fact, and the rules recovered from it. If *no*
alternative exists, the machine doesn't invent a happy ending either: the effect
simply stays unachieved, and it can tell you so. Same honesty as `unknown`, now
pointed at *doing* instead of *knowing*.

## Not a new way of thinking

You might expect all this — sequencing, planning around gaps, detecting failure,
replanning — to be some big new subsystem. It isn't, and that's rather the point.
[Chapter 18](../deep/18-modes.md) made a promise: following a procedure is **never** a
new mode of thought, only a **composition** of the handful the machine already has.
Step through a sequence (iterate), make a call (act), check the result (test),
react to what you find (more rules). Everything in this chapter is those pieces,
snapped together in the knowledge base — not one new line in the engine.

That's why the same three virtues you've watched all along carry over intact. The
machine that **explains** its answers explains its actions the same way. The
machine that says **`unknown`** rather than guess says *"that step didn't take"*
rather than pretend. And the machine that grew new abilities by being *told* things,
not rebuilt, grew *this* one the same way. It doesn't just know out loud. It gets
things done out loud, too.

## Watch it happen

The [procedures playground](../playground/procedures.md) lets you author a routine,
run it, and watch the steps go by — including the one the machine slips in for
itself. Then flip a step to **fail** and watch the machine notice, set it aside,
and recover through another route. Same facts, same rules; you're just changing
what the world hands back.

---

**Next:** the grand reveal — the tiny machine that's been running under
*everything* you've seen.
[The machine underneath →](16-the-machine-underneath.md)

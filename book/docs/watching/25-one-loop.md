# One loop, and everything on it

Every chapter so far has quietly assumed the machine does one thing at a time,
start to finish. Ask it to build a tower and it builds the tower; you get control
back when it's done.

That assumption has been hiding something, and this chapter removes it.

## The test

Here is a question worth asking of any system that claims its reasoning is
inspectable:

> **Can it be stopped between any two primitive steps, and can it say what it was
> doing at that moment?**

It's a good test because it can't be passed with a slogan. Either the state of a
half-finished computation is something you can point at, or it lives in the
machinery and the honest answer is *no*.

Until recently the answer here was no, and in an embarrassing place. The
instruction set of Chapter 20 ran in a plain loop: a program counter in a local
variable, registers in a dictionary, going round until the program finished.
Everything *it* worked on was inspectable data. The thing doing the working was
not.

## What had to become data

Four things, and the fourth is the one that hides.

| what | why it's needed |
|---|---|
| the program counter | *which instruction is next* |
| the stack | *what called this* |
| the registers | *what it has worked out so far* |
| **the focus** | *what it is pointed at* |

The first three are obvious. The fourth had been sitting in plain sight
describing itself as a virtue: the focus — the thing that says which nodes a rule
is currently aimed at — "holds no graph state itself".

That's the defect stated as a feature. Chapter 13 exists because *attention was
not data*. It fixed the record of attention **shifts** while leaving the pointers
themselves in an object that was created per call and thrown away.

Now a paused program is an ordinary node:

```
count_wheels @4/9: JMPNOT
pc: 4   halted: False
```

You can read that with the same instructions any rule uses on any other node. No
new opcode was added to make it possible — which is the same evidence Chapter 13
offered for the thread, and the same argument gets to be reused because the
substrate really is the same.

!!! note "Measured, because the alternative was a trap"
    The tempting thing to say is *keep the fast Python loop for the common case,
    materialise only when someone's watching*. That builds two machines and makes
    the honest one the exception.

    So it was measured instead. Every register read and write now goes through
    the graph, and the full self-test runs in **7.4 seconds against 7.2**. There
    are few registers per program and the reads are short. The argument for the
    fast path was never tested and turned out to be worth nothing.

## One agenda

Once a half-run program is a node, running *two* of them is not a new capability
that needs building. It's a list.

An **agenda** holds tasks. One **tick** takes the task at the front, advances it
by exactly one primitive step, and puts it at the **back**. That's the loop.

Four kinds of work now sit on it, and they're all the same shape:

| task | one primitive step is |
|---|---|
| a running program | one instruction |
| a search | one imagined state |
| carrying out a plan | one real action |
| pursuing a goal | one step of plan / act / check / replan |

Adding a new kind of work means writing *its* step. It never means touching the
loop.

**And the rotation is the data.** Interleaving isn't a policy the loop
implements; it's what falls out of the agenda being an ordered list that gets
rotated. *Which task is next* is a question anyone can ask of the graph, not a
fact hidden in a scheduler.

Here are two entirely unrelated tasks — a little program counting wheels, and a
goal being pursued — scheduled together:

```
run      activation  count_wheels @0/9: CONST
imagine  pursuit     pursuing 'build a tower', attempt 1: planning
run      activation  count_wheels @1/9: COUNT
imagine  pursuit     pursuing 'build a tower', attempt 1: planning (0 states imagined)
run      activation  count_wheels @2/9: LABEL .loop
imagine  pursuit     pursuing 'build a tower', attempt 1: planning (1 states imagined)
run      activation  count_wheels @3/9: LT
act      pursuit     pursuing 'build a tower', attempt 1: acting (step 0 of 2)
```

They alternate, and at every line the machine can say what it is about to do.

!!! warning "A tick of a pursuit is not 'one attempt'"
    This is the easy version, and it would have been wrong. An attempt contains a
    whole search *and* a whole carrying-out. So a pursuit holds a current
    sub-task, and advancing the pursuit advances **that** by one primitive step.

    Changing phase costs a tick of its own, deliberately — *"the plan is in hand
    and nothing has been done yet"* is a state the machine may legitimately be
    stopped in. It is the last moment before anything becomes irreversible.

## The one thing that must not become uniform

Look at that trace again, at the left column.

Three of those steps say `imagine` or `run`. One says **`act`**. And that
difference is the whole reason the uniformity elsewhere is safe.

Making everything one kind of task is tidy. Making *every step equally
reversible* is a lie, because they aren't: imagining a move costs time, and
taking one cannot be undone. So the loop can be asked, **before** a step is
taken, what kind of step it would be:

```
act   pursuit   pursuing 'build a tower', attempt 1: acting (step 0 of 2)
^^ STOP: this one cannot be taken back
```

Stop there, and the world is genuinely untouched — the blocks are where they
started. Let it carry on, and it builds the tower.

Two details of that design are deliberate.

**A tool declares whether it looks or acts, and the default is the unsafe one.**
A directory scan and a sent email were previously the same thing to this
machinery. Now a tool can say `observes=True` — and anything that doesn't say is
assumed to **act**. Being wrong that way costs a pause. Being wrong the other way
spends an irreversible action somebody meant to withhold.

**Declining is the caller's move, not the loop's.** The loop advances the head of
the agenda; it does not decide on your behalf that you would rather not. Stopping
before an action means reading the verb and simply not calling for the next tick.
The asymmetry is the point: the machine will tell you what it's about to do, and
it will not pretend to know whether you want it.

## Three levels, all ticking

The best evidence that this is real rather than cosmetic is a program that ought
to break it.

`think` is a rule that spins in a loop until its search finishes — a blocking
program by any ordinary reading. Under the old arrangement it held the machine
hostage: an interruptible search, driven from inside an invocation that could not
itself be interrupted.

Now it doesn't. The loop advances the *program* one instruction at a time; that
instruction advances the *search* one imagined state at a time; and unrelated
work on the agenda runs in between — while `think`'s search is still open, not
merely before or after it.

Three levels of stepping compose. So a rule does **not** have to be rewritten in
some awkward style to stop holding the loop, which is just as well, because that
cost would have been paid by every author of every rule, forever.

!!! note "The refusal at the boundary"
    The loop will not drive a program that exists only as a Python object rather
    than as stored text. It says so and stops.

    That looks unhelpful until you ask what resuming one would mean: nothing
    could reconstruct it except the caller holding it, which makes it exactly the
    unreachable island this whole design exists to avoid. The same program,
    *stored*, is driven without complaint — so the refusal is about being
    reconstructable, not about programs.

---

**Next:** now that a running computation is something the machine can read, it
can have opinions about one. [Noticing it's taking too long →](26-taking-too-long.md)

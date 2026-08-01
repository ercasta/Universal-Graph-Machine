# Recipes, and rules you must follow

A guideline can only reorder. This chapter is about authored knowledge that
**replaces the search** — and about the one distinction that everything here
turns on, which is not the one people expect.

## A recipe

```
method stack by clearing:
    handles link on
    because a block only goes onto a clear one
    step object.clear = true
    step subject on object
```

Read it as: *whenever the goal wants an `on` link between two things, do these
two things in this order — first make the destination clear, then stack.*

Hand the machine a goal it fits:

```
goal put a onto b:
    a on b
```

and instead of enumerating every move it could make and scoring them, it raises
two subgoals and works on those:

```
subgoals raised: ['step object.clear = true', 'step subject on object']
{'done': True, 'method': 'method#7692'}   |  a on b: True
```

The world really changed — `a` really is on `b` — and the record says which
recipe did it.

## Why this can't be expressed as advice

Chapter 17's guidelines reorder a list of candidate moves. A recipe **doesn't
produce a list**. It replaces the enumeration with two subgoals, and the whole
subtree of alternatives that enumeration would have generated never exists.

That's where the large win lives. It's also why it's dangerous, and the danger
is a new one:

| kind | worst case if you're wrong |
|---|---|
| guideline | the search takes longer |
| `never` constraint | a goal is honestly unreachable, and it says so |
| **recipe** | a goal that *was* reachable becomes unreachable |

A guideline literally cannot lose you a solution (Chapter 17). A recipe can,
because it prunes on **authority** — your say-so about the sanctioned way — and
not on evidence or proof. That's a third kind of justification, and it deserves
to be named rather than smuggled in as a very strong hint.

The safety net is the next section.

## Force: what happens when it *doesn't* work

Here are two decompositions. They are identical in every respect — same steps,
same order, same goal — except for one declared word:

```
method the approved way:          procedure the approved way:
    handles link on                   handles link on
    step object.clear = true          step object.clear = true
    step subject on object            step subject on object
```

Now give each of them a case where the first step works and the second one
cannot be achieved by anything the machine knows:

```
method   : {'done': False, 'fell_back': True,  'force': 'advisory'}
procedure: {'done': False, 'stopped': 'refuse', 'force': 'mandatory'}
           why: the procedure's step 'the impossible bit' did not succeed,
                and a mandatory decomposition may not be worked around
```

The **method** gives up on the recipe and goes back to searching for the goal
the ordinary way. The **procedure** refuses, names the step that stopped it, and
does not look for another route.

> **Force is not about strength. It's about failure.**

That's the sentence to keep. Two pieces of authored knowledge can be written
identically and behave oppositely, and what separates them is not how confident
you are — it's what you want to happen when the world doesn't cooperate.

And it can't be guessed from the content, which is why the surface makes you
type the word `method` or the word `procedure` rather than inferring one.

## Why refusing is ever the right answer

This inverts every reflex the machine has. Chapter 10 replans when reality
disagrees. Chapter 11 reaches for a contingency. Chapter 7 keeps searching. The
whole disposition of the thing is *find another way*.

For a procedure, finding another way is precisely the forbidden act.

If the sanctioned procedure for handling a customer's data is these four steps
in this order, then a plan that achieves the same outcome by some other route
isn't a clever success. It's an unlogged, unapproved, undefendable act that
happened to work. So:

> For a procedure, **"I couldn't do it" is a better outcome than "I did it
> another way."**

Which is also why a refusal reports differently from a failed search. One says
the world wouldn't permit it. The other says *we were not permitted to try*.
Collapsing them would throw away the only fact that matters afterwards.

!!! warning "Advisory doesn't leak upward"
    Put an advisory method inside a mandatory procedure and it stays contained.
    Force is read from the parent whose decomposition it is, never from the step
    that failed — otherwise a mandatory procedure with one advisory sub-recipe
    would quietly become improvisable one level down, which is exactly the hole
    a compliance story cannot have.

## Goals inside goals

All of this needed something the machine didn't have until recently: goals that
can contain other goals.

A subgoal points at its **parent**, so *"am I inside a procedure right now?"* is
a walk up a short chain — and that's the question a rule actually asks. Children
are cheap to find the other way round too, and a cycle is structurally
impossible, because a goal's parent is fixed the moment it's created and a brand
new goal can't already be its own ancestor.

That last one bounds cycles but **not depth**. A recipe that raises a goal that
matches the same recipe again is how repetition gets expressed, and it's also
how the whole thing runs forever. That remains an open problem, honestly.

!!! note "Deep dive: the trap that was waiting in the parent"
    *Is this goal done?* for a goal with children is naturally written as: no
    child of mine is unfinished.

    Which is **true before any child exists**. An undecomposed goal reads as
    trivially achieved — the machine congratulating itself for a plan it hasn't
    made. This exact bug had been found and written up in earlier work on this
    project long before this chapter existed; going back and reading those
    notes first is what caught it here — in *two* places rather than one, since
    the same mistake was available one level down and had only ever been fixed
    at the other.

    The general form is worth stealing: **don't trust an open-ended absence
    without an explicit fact saying the list is closed.** "Nothing contradicts
    it" and "it's true" are the same shrug the machine spends Chapter 3
    refusing to make.

!!! note "Deep dive: a route, not a redefinition"
    The first version of recipes had a subtle and expensive bug. When a recipe
    decomposed a goal, it also rewrote how that goal counted as achieved: *this
    goal is done when its steps are done*.

    Reasonable, until an advisory recipe fails and falls back to searching. Now
    the goal's own criterion has been overwritten with "my steps are complete" —
    and its steps are the ones that just failed. The goal could no longer be
    satisfied **by any route at all**. The decomposition had silently destroyed
    the escape hatch that makes authority safe in the first place.

    The fix: a goal that has its own conditions keeps them. Only a goal with no
    conditions of its own — *"do these steps, in this order"*, which really is
    the whole of what it is — gets judged by its steps.

## The one you're told, and the one you must not be told

Both examples in this chapter came in as text, and that's not incidental. The
same small language carries goals, guidelines and recipes, and the parser can
refuse:

```
- `method empty` has no steps; it would decompose into nothing
- 'a' is not a role — a step may only speak of subject or object,
  never a named individual
- `prefer nothing` names neither an action nor a thing —
  advice that matches everything is not advice
```

That middle one is the interesting refusal. A step says *the subject of the
matched condition*, never *the crate called `a`* — because a recipe that named a
particular crate would be about that crate, and couldn't be reused anywhere
else. The same reason a type in Chapter 21 can't name a specific thing either.

And a refusal leaves nothing behind. Half a parsed recipe doesn't linger in the
graph to be matched against something later.

---

**Next:** the machine can now be told what to do and what not to work around.
One thing is still missing, and it's the difference between *there's nothing
there* and *I haven't looked*. [Not knowing →](19-not-knowing.md)

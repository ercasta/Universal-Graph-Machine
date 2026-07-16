# A rule is a little program

!!! note "You've reached the bonus floor"
    Part 3 already gave you the whole machine, top to bottom — you can stop there
    and have the complete picture. **Part 4 is for the curious**: it opens the hood
    one more turn and shows the actual gears. Nothing here changes how you *use* the
    machine; it's here because some people can't help but ask "yes, but how, really?"

In Chapter 15 we said a rule becomes a tiny two-step program — **match**, then
**apply** — running on a small set of instructions. That was true, but we waved a
hand at what the instructions actually *are*. Let's name them. There aren't many,
and once you've seen them, the phrase "it's all just dots and arrows" stops being
a slogan and becomes something you could almost run by hand.

## Look first, then write

Every rule splits into two phases, and the order is sacred:

1. **Match** — go *looking* through the graph for the pattern in the condition.
   This phase reads only. It never adds or changes a single arrow.
2. **Apply** — for each match found, *write* the conclusion. This is the only
   phase that changes anything.

Why so strict? Because a rule that wrote while it was still looking could trip
over its own output — conclude something, then "discover" the thing it just wrote
and conclude again, forever. Looking and writing are kept on opposite sides of a
fence, and the machine refuses any program that puts a *look* after a *write*.

## The verbs of looking

The match phase is built from a handful of verbs. In plain language:

- **find** — sweep up every dot carrying a certain mark. *"Find everything tagged
  `suspect`."* This is where a search starts. (The real opcode is `SEED`.)
- **follow** — step along an arrow from a dot to its neighbour. *"From bo, follow
  the `in` arrow"* → the library. (`FOLLOW`.)
- **check** — does this dot carry a mark? Keep it if so. (`TEST`.) And its crucial
  twin: **check-absent** — keep the dot *only if it does **not** carry the mark*.
  That one little inversion is the whole engine of "not": when the machine decides
  cy is **not** cleared, it's a check-absent that came up empty.
- **same? / different?** — are these two dots actually the same one? Or provably
  different ones? (`SAME` / `DISTINCT`.) This is how identity (Chapter 12) is
  enforced down at the metal.

There are a few more for shades of grey — matching a degree rather than a plain
yes/no, or joining two dots that merely *agree on a value* — but those five are
the backbone. Everything the machine "notices" is some sequence of *find, follow,
check*.

## The verbs of writing

The apply phase is even smaller:

- **make** — mint a brand-new dot and wire arrows to it. This is how a fresh
  conclusion, or a reified "so-and-so did such-and-such," comes into being.
  (`MINT`.)
- **write** — stick a mark on a dot: *"bo is `cleared`."* A new fact, added to
  the graph. (`EMIT`.)

That's the pair that does all the *concluding*. Notice what's **not** here: there
is no "erase a fact" verb in this vocabulary at all. Ordinary reasoning can only
ever *add* — which is exactly why the because-trail (Chapter 8) never has to worry
about a fact quietly vanishing out from under it. (There *is* a real deletion
instruction, but ordinary rules can't reach it — that's a firmware matter we'll
get to in Chapter 19.)

So our familiar rule —

```
?someone is cleared when ?someone is alibied
```

— compiles to roughly: **find** everyone tagged `alibied`; then, for each, **write**
`cleared` on them. Read that twice and you've read an interpreter.

## The second level: a finger on the current line

A single match-then-apply is one straight run — look, write, done. But real
reasoning needs to *loop* ("try each suspect"), and to *stop mid-thought to ask a
sub-question* ("…but first, is cy cleared?"). A straight run can't do that on its
own. So above the instructions sits a second, thin layer of control — think of it
as **a to-do list with a finger pointing at the current line**, plus a few ways to
move the finger:

- **jump** to another line (so you can loop back and do a block again).
- **jump *if*** a counter is still positive (so a loop knows when to stop).
- **call** and **return** — step into a sub-task, keeping a stack of where to come
  back to. This is how the machine asks itself a question in the middle of
  answering another one, to any depth.
- **suspend** and **resume** — *pause the entire machine*, hand a request to the
  outside world, and later pick up at the exact instruction where it stopped.

That last pair is quietly the most important. **Suspend/resume is the mechanism
behind "let me find out."** When the machine hits a fact it doesn't have
(Chapter 13), it doesn't crash and it doesn't guess — it suspends, states exactly
what it needs, and waits. Give it the answer and it resumes as if nothing
happened. The same trick lets it duck into a "suppose" and come back.

## Two levels, one machine

So there are really *two* little programs stacked on each other: the **instructions**
that do the work (find, follow, check, make, write) and the **control** that decides
which instruction runs next (jump, call, return, suspend). Early on, that control
was faked with ordinary Python — `for` loops and function calls in the code around
the engine. The deeper design move was to turn *even the control* into instructions
the machine runs, so that "how it thinks" lives in the same visible, inspectable
place as "what it thinks." Nothing about the reasoning hides in a language the
graph can't see.

The complete list — every looking-verb, every writing-verb, and every control
transfer — fits comfortably on one page. You'll find it laid out in the
[appendix](../appendix/index.md#the-instruction-set-the-data-path).

---

**Next:** we've named the instructions. But *when* does the machine reach for
each — when does it loop, when does it suppose, when does it just look? That turns
out to be a short, closed list too. [Nine ways to think →](17-modes.md)

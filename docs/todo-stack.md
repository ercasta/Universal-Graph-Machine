# The todo stack

Shipped, not a proposal. `ugm/rules/todo.ugm` is the corpus; `todo_stack()` in `selftest.py` runs it.

## The pattern

A standing anchor, `internal_todo`, with tasks pushed onto it and popped off it as a stack. Two
pieces, no new engine primitive:

- **A channel arrival opens a task.** System-wide: whatever arrives, answering it becomes an open
  task (`task($t)`, `about($t, $said)`).
- **A judge rule closes it.** `todo.ugm` writes no closing rule of its own — deciding a task is done
  is the host corpus's business, the same reason `bundle.ugm` carries no policy either. A host corpus
  writes an ordinary rule that concludes `completed($t)`.

```
say ops: +cancelled(bl204)

rule <trust>
  +says($ch, $p)
  no trusted($ch, $p)
->
  +trusted($ch, $p)
  +$p

rule <task-answered>
  +about($t, $said)
  keep believed($said)
  no completed($t)
->
  +completed($t)
```

`keep` on `believed($said)`: firing spends what it matched, and this judge is not the rule that
should retire the belief — only the one reading it to decide a task is answered.

Load it alongside your own corpus with the **same `scope=`**, the same discipline
[`tools-approval.md`](tools-approval.md) needs — `task(...)` in each file mints a twin nobody's rules
can see otherwise.

## Why a stack

`internal_todo` is a sentinel: `top(internal_todo, internal_todo)` is the empty-stack base case, so
pushing the first task and popping the last are the same code as every push and pop between them. A
task marked `completed` does not have to be the current top to be closed — closing something buried
is ordinary business — but the stack only answers for what's on top, skipping over anything already
closed the moment it's reached.

## Keeping a task open

There used to be a third piece: a `brush` lane whose one rule re-attended the top open task every
round, so the same application kept surviving the per-tick pick instead of being consumed once and
never seen again. Both halves of that are gone — no pick, no focus pool — and what replaces it is
smaller:

- **`keep` on `top(internal_todo, $t)` and `task($t)`** — read without spending, so the stack's own
  pointer and its own record stay on.
- **Every rule that matches fires.** A corpus's own rules answering `about($t, $said)` get a reason to
  consider `$t` on every tick it is open, for free, however many times they match without yet closing
  it.

## What's out of scope here

What counts as "done" is not this file's call. Neither is when to escalate, retry, or give up on a
task that never closes — a host corpus's own policy, the same way `bundle.ugm` carries none either.

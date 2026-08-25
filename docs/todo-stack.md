# The todo stack

Shipped, not a proposal. `ugm/rules/todo.ugm` is the corpus; `todo_stack()` in `selftest.py` runs it.

## The pattern

A standing anchor, `internal_todo`, always attentioned. Tasks are pushed onto it and popped off it as
a stack. Three pieces, no new engine primitive:

- **A channel arrival opens a task.** System-wide: whatever arrives, answering it becomes an open
  task (`task($t)`, `about($t, $said)`).
- **A `brush` lane keeps the top task in mind.** One rule, its own lane, re-attends the current top
  task every round — so a corpus's own rules keep getting a reason to consider it, however many times
  they match without yet closing it.
- **A `judge` lane closes it.** `todo.ugm` writes no closing rule of its own — deciding a task is done
  is the host corpus's business, the same reason `bundle.ugm` carries no policy either. A host corpus
  writes an ordinary rule that concludes `completed($t)`, in the `judge` lane.

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
  +says($channel, $said)
  +believed($said)
  no completed($t)
->
  +completed($t)
fact +lane(<task-answered>, judge)
```

Load it alongside your own corpus with the **same `scope=`**, the same discipline
[`tools-approval.md`](tools-approval.md) needs — `task(...)` in each file mints a twin nobody's rules
can see otherwise.

## Why a stack

`internal_todo` is a sentinel: `top(internal_todo, internal_todo)` is the empty-stack base case, so
pushing the first task and popping the last are the same code as every push and pop between them. A
task marked `completed` does not have to be the current top to be closed — closing something buried
is ordinary business — but the stack only answers for what's on top, skipping over anything already
closed the moment it's reached.

## Attention, restored

Decay is live (`ugm/core/attention.py`): a claim fades on its own clock rather than sitting at full
strength forever. Two consequences this corpus leans on:

- **A loaded `fact` gets no attention.** Attending is *taking care of something*; background nobody
  has been asked to take care of stays background. `internal_todo`'s own pin comes from an arrival
  this file delivers itself (`say todo: +boot`), not from being loaded.
- **Several ground things landing together can starve each other.** The engine re-attends a matched
  sibling that lost its turn (a genuine revisit, never downgrading a stronger claim), but a rule
  writing something an ordinary write only holds for one tick — `<intake>`'s own `says(...)`, this
  file's own `task(...)` — can still lose a race to a busy round. `<open-task>` gets its own lane for
  exactly this reason (`todo.ugm`'s own header spells out the measurement); a host corpus's `<trust>`
  rule may need the same `after <intake> { $sp = says($channel, $said) } => attend($sp, 5, 1, 1)` hop
  `delay.ugm` needed once its own facts stopped being loaded pre-attended.

## What's out of scope here

What counts as "done" is not this file's call. Neither is when to escalate, retry, or give up on a
task that never closes — a host corpus's own policy, the same way `bundle.ugm` carries none either.

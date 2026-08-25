# Learning

Everything up to here takes the rule set as given. A corpus is authored, the
bundle ships, and the agent's cleverness is entirely in what it does with what
it was handed.

The rules themselves don't change. What changes is which postconditions a
rule's `after` clause spends, and by how much — and there is exactly one
mechanism for that today: `learned`.

## `learned after`

A postcondition clause can be marked `learned`. Marking it says: this spend
was put here by a calibration process, not by the corpus's ordinary logic —
readable the same way as any other clause, but tagged as tunable.

```
rule <move> = implies(
    { +enemy($x), +wounded($x), no covered($x) },
    { +covered($x) } )

learned after <move> { +covered($d) } => attend($d, 3)
```

Run for real:

```
learned.ugm: 2 ticks, ended quiescent

what it believes, newest first:
  covered(orc1)
  wounded(orc1)
  enemy(orc1)
```

`frozen` marks the opposite of `learned` — a clause calibration may not
touch. Both keywords are read by `ugm/core/text.py`, and both are the whole of
what "learning" means in the engine as shipped.

A lesson names a **thing** (`attend($x)`), never a rule — which is what lets
a lesson survive the corpus being edited. A rule's `after` clauses can be
rewritten, added to, or reordered without invalidating a lesson attached
somewhere else, because the lesson was never about the rule's identity.

## Where the calibration itself comes from

Nothing in this repository proposes or writes a `learned` clause
automatically. The mechanism reads and respects the tag; producing the tagged
value is a corpus author's job, done by hand — from watching a run, from a
transcript, from trial and error on the scoring the table (Chapter 28) uses.

!!! note "Idea: gates, and an analog guard against runaways"
    Attention already reads as a gate: a rule can't fire on an antecedent
    member nothing has attended to, and `attend`/`unattend` are a rule's RHS
    turning a node on or off for whatever reads it next.

    That reading only needs presence — `attention(x)` holds or it doesn't.
    Nothing forces the gate to stay binary. If a gate carried an intensity
    instead of on/off, a rule that risks running away could maintain its own
    guard node, raising that node's intensity by one each tick it fires, and
    gate its own antecedent on the guard staying under a threshold —
    self-limiting, rather than caught only by `bounded(ticks)` after the fact
    (Chapter 34's "Loop detection").

    Picking among rival rules doesn't need the engine's attention mechanism
    at all — the same gate pattern, run entirely in the corpus. Mint an
    anonymous node per rule to bias (`gate(19043)`, a numeral carrying no
    meaning of its own), add it to that rule's antecedent, and let a
    separate rule's consequent be the only thing that asserts or denies it.
    A "style" is then learned by wiring gate members onto existing rules'
    antecedents — additively, the same as any other clause — without ever
    naming the rule being steered. That keeps the same property `attend($x)`
    already has: the thing doing the steering never has to cite the rule it
    steers.

    None of analog intensity, a runaway guard, or corpus-level gating like
    this is built. Marked here as an idea, not a result.

---

**Next:** the five things that genuinely could not be taught.
[What cannot be a convention →](../floor/30-the-floor.md)

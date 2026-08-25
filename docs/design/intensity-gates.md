# Intensity gates — experimental substrate redesign

Status: exploratory, nothing below is implemented. Branch: `intensity-gates`.

This is not a shipped-docs page (`book/docs/...`) — those claims are backed by
a runnable check. This one isn't, yet.

## What replaces what

| today | intensity-gates |
|---|---|
| `believed(p)` / `erase` — presence, kept as an occasion stack | every node carries an intensity (a number); "on" = intensity above a threshold |
| `attention(x)` — a separate lift/pick layer over the table | gone — an antecedent member reads a node's intensity directly |
| lanes | gone — nothing needs a guaranteed turn once firing is per-rule rather than per-table: a rule fires whenever its own gates are on, so it can't be starved by another rule's schedule |
| score / `standing` / declaration-order tie-break | gone — a rule doesn't "win" a tick against rivals; every rule whose gates are on fires |
| gate node (learning doc, ch. 29) | an ordinary node with no domain meaning (`gate(19043)`), wiring one rule's output to another rule's input |

## Firing

- A tick evaluates every rule whose full set of antecedent nodes is on — not
  the top of a ranked table.
- A rule needing several nodes on (`{gate(1), gate(2)}`) doesn't fire until
  every one of them is — the AND does the synchronizing; nothing schedules,
  nothing picks.
- Firing order within a tick must not change the end state.

## RHS

- A postcondition can set a node's intensity, not just assert or deny it.
- The runaway-guard idea (learning doc, ch. 29): a rule reads its own guard
  node's current intensity, writes back +1, and gates its own antecedent on
  the guard staying under a threshold.
- The rule-bias idea (same note): wire a `gate(n)` node into an existing
  rule's antecedent; a separate rule's RHS is the only thing that sets it.
  Style is learned by adding these, never by naming the rule being steered.

## First-cut defaults — flagged, not settled

**Same-node, same-tick writes combine by taking the max.** Two rules fire in
one tick and both set node `p`'s intensity — the higher one wins, regardless
of which rule ran first. Deterministic, order-independent, and needs no
decay bookkeeping of its own. Sum was the alternative and was set aside for
now: it would make the result depend on *how many* rules fired, not just on
what they said, and it needs a decay policy to keep from saturating.

**Occasions survive.** Belief today keeps more than presence — the same
proposition can be believed more than once (an occasion stack), and push/pop
frames (ch. 25) rest on that. First cut: a node keeps its occasion stack, and
each occasion carries its own intensity, rather than intensity collapsing
occasions into one number.

**Intensity only changes when an RHS sets it.** No automatic decay per tick.
The runaway guard's "+1 each tick it fires" is the corpus doing that by hand,
not the substrate doing it for free. A decay primitive is a plausible later
addition, not assumed here.

**Surface syntax stays close to today's.** `+p(x)` in an antecedent still
reads as "p(x) is on"; `no p(x)` still reads as "not on." A new form exposes
the number itself for the guard/gate-bias cases — read the current
intensity, write a new one — syntax not yet chosen.

**Ticks stay discrete.** What changes is that a tick can fire more than one
rule, not exactly one.

## Open questions, not defaulted

- Does every node get an intensity (domain propositions included), or only
  ones a corpus explicitly opts into? "we don't need believed in the engine"
  reads as: every node, uniformly.
- What does `-p(x)` — an explicit denial, distinct from `no p(x)`'s silence —
  become once presence is gone?

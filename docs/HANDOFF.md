# Handoff — 2026-08-24 (attention as tokens)

    python -m ugm.selftest    193 checks, 10 failing    <- RED, deliberately

Red is the state, not an accident. `tokens` (0ecc7d4) is a checkpoint of a
migration in progress, with the known bugs listed below.

## The line this session took

Attention stopped being a decaying score and became a consumable.

- a move **consumes** what it matched on, globally. One occasion, one use.
- what a move writes is new business and gets a token.
- `brush($x)` on the RHS puts one back. Whether others still want a thing is
  a fact about the move, not about the line — `<trust-user>` knows believing
  you is not the end of what you said.
- no decay, no lifespan. Attention is not memory; it is what is still to do.

Fixed by construction, after five configurations of a decay constant could
not fix them by tuning:

- `worked.ugm` — `<boil>` and `<weather>` both fire.
- an oscillating corpus terminates instead of running to the tick bound.
- harneskills works with **one** brush, on `<trust-user>`.

## Known bugs (most of the 10)

- `_attend_written` re-attends what a move **erased**, so a rule that
  consumes and erases the same proposition puts the token straight back.
  `want(deploy(web))` stays attended after `<request>` matched and erased it.
- a tool's answer lands **no token**. `answered(approve, ...)` is believed and
  absent from the pool, so `<approved>` is never enabled.
- `unattended` now fires as the ordinary terminal state — spent occasions are
  what ending looks like. Its checks want revisiting.

## Next: never intern

`Graph.rel` interns; it should not. RHS decides when to create a node and
when to intern.

This sits **underneath** the token work: a token is per occasion, and
occasions cannot be distinct while structure is identity. It is the same
root as "a sentence said twice writes nothing".

Smaller than it looks:

- `-p(a)` is not a thing. The RHS destroys nodes the LHS **bound**, so
  erasure needs no structural search.
- absence is already structural — the matcher asks `pad.holds_any`, written
  because `instance` could already mint a second `p(x)` beside the interned
  one. Un-interning makes that the normal case.
- what remains: sites that **build** a node then ask `holds` (they want
  `holds_any`), `_merges`/`_key` retiring with the intern table, and
  confirming `candidates()` never assumes one node per shape.

Suggested order: the two token bugs first (independent, cheap), then this as
its own line — query layer before the graph stops helping.

## Also built

- **per-line scoring** — `$z = intake($x, $y) [+3, attention_multiplier:1.2]`.
  A bracket is a score, never a filter; all lines still match. The multiplier
  hangs on **what the line bound**, so a rule can say attention on the event
  matters and attention on the participants does not.
- **calibration** (`ugm/learning/`) — an episode is one `.ugm` file: starting
  condition, what is in mind, and the judge. Mutators move numbers only. A
  missing verdict is a failure, because a judge is ordinary rules and a
  calibration could otherwise starve the thing scoring it. No held-out set,
  so a result is a claim about those episodes.
- **gates**, tracked in `mutate`'s docstring and not built: a synthetic
  proposition threaded RHS to LHS, for where a data dependency does not order
  two rules. Structural, so out of the numbers-only phase.

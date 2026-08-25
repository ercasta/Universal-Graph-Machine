# Intensity gates — the substrate

Status: **built.** `python -m ugm.core.firing` is one runnable
demonstration per claim in "Firing" and "RHS" below; `python -m ugm.selftest`
covers the rest.

`book/docs/...` has NOT been ported — those chapters still describe the ranked
table, the focus queue and the frame stack, all of which are gone. Read this
page over them until they are rewritten.

## What replaces what

| today | intensity-gates |
|---|---|
| `believed(p)` / `erase` — presence, kept as an occasion stack | every node, uniformly, carries an intensity (a number); "on" = above a threshold; `erase`'s job is now setting it to `0` |
| `attention(x)` — a separate lift/pick layer over the table | gone — an antecedent member reads a node's intensity directly |
| the FOCUS system — `attend`/`brush`/`unattend` as postconditions, `attentioned($x)` as a predicate, a decaying queue on `Machine` | gone — *in play* is *on*, which is what an ordinary member already asks |
| FRAMES — `push`/`pop`, a stack of sub-lines of work, each with its own attention queue and standing weights | gone — there is no queue to suspend, and nothing schedules, so there is no line of work to put away |
| lanes | gone — nothing needs a guaranteed turn once firing is per-rule rather than per-table: a rule fires whenever its own gates are on, so it can't be starved by another rule's schedule |
| score / `standing` / declaration-order tie-break | gone — a rule doesn't "win" a tick against rivals; every rule whose gates are on fires |
| gate node (learning doc, ch. 29) | an ordinary node with no domain meaning (`gate(19043)`), wiring one rule's output to another rule's input |
| write-time TRIGGERS — `intercepts`/`producing`/`instead`/`drop`/`rewrote`, and the `after <R> { ... } => ...` statement | gone — gating moved into the governed rule's own antecedent, where a reader can see it |

## Firing

- A tick evaluates every rule whose full set of antecedent nodes is on — not
  the top of a ranked table.
- A rule needing several nodes on (`{gate(1), gate(2)}`) doesn't fire until
  every one of them is — the AND does the synchronizing; nothing schedules,
  nothing picks.
- Firing order within a tick must not change the end state.
- **A rule consumes its inputs by default.** Firing discharges every
  antecedent node it matched — each goes back to "off" — unless the rule's
  own RHS recharges it. This is Petri-net firing semantics (consume from
  input places, produce to output places) applied to an analog value instead
  of a token count; the runaway guard is the RHS reading its own discharged
  value and writing back `+1` instead of leaving it spent. It also means the
  "guarded rule doesn't re-derive what it already derived" pattern
  (watching/25-own-state.md) stops being something a corpus has to write by
  hand — consumption is what would make re-matching the same input
  impossible without something recharging it first.
- **A member can opt out, per line.** A modifier on one antecedent member
  reads it without discharging it — a non-consuming check, same as a Petri
  net's test arc. Strawman syntax, not settled: `keep enemy($x)` inside the
  antecedent, discharge being what a plain `+enemy($x)` still does. This is
  the escape hatch for a fact meant to be read by more than one rule without
  every reader having to recharge it back.

## RHS

- A postcondition can set a node's intensity, not just assert or deny it.
- The runaway-guard idea (learning doc, ch. 29): a rule reads its own guard
  node's current intensity, writes back +1, and gates its own antecedent on
  the guard staying under a threshold.
- The rule-bias idea (same note): wire a `gate(n)` node into an existing
  rule's antecedent; a separate rule's RHS is the only thing that sets it.
  Style is learned by adding these, never by naming the rule being steered.
- **`-p`, today's erase sign, is retired as its own primitive.** It's
  subsumed by the general intensity write: setting a node's intensity to `0`
  is what un-claiming it now means, and it does exactly what `erase` does
  today — the node survives as structure, nameable and matchable, just off.
  `destroy($x)` stays a separate, existing postcondition (ch. 28's list) for
  the harder operation `-p` was never asked to do: taking the node out of
  the graph entirely, not just switching it off.

## First-cut defaults — flagged, not settled

**Same-node, same-tick writes combine by taking the max.** Two rules fire in
one tick and both set node `p`'s intensity — the higher one wins, regardless
of which rule ran first. Deterministic, order-independent, and needs no
decay bookkeeping of its own. Sum was the alternative and was set aside for
now: it would make the result depend on *how many* rules fired, not just on
what they said, and it needs a decay policy to keep from saturating.

**Occasions survive.** Belief keeps more than presence — the same proposition
can be believed more than once (an occasion stack). A node keeps its occasion
stack, and each occasion carries its own intensity, rather than intensity
collapsing occasions into one number. Push/pop FRAMES (ch. 25) used to rest on
this too, and are retired: a frame was a suspended attention queue, and there
is no queue.

**No ambient time-decay.** A node's intensity doesn't erode on its own each
tick just for existing. The only two things that move it are consumption
(discharge on firing, above) and an RHS explicitly setting it — the runaway
guard's "+1 each tick it fires" is the corpus writing that increment, not the
substrate leaking it for free.

**Surface syntax stays close to today's.** `+p(x)` in an antecedent still
reads as "p(x) is on"; `no p(x)` still reads as "not on." A new form exposes
the number itself for the guard/gate-bias cases — read the current
intensity, write a new one — syntax not yet chosen.

**Ticks stay discrete.** What changes is that a tick can fire more than one
rule, not exactly one.

**Discharge is universal, not gate-only, with a per-line opt-out.** Every
matched antecedent member is spent by default — a plain fact like
`enemy($x)` goes the same way a gate node does — because that's what makes
the opt-out (`keep`, above) a real choice rather than a distinction without
a difference. A corpus that wants today's persistence for a given fact
writes `keep` where it reads that fact; a corpus that writes nothing gets
resource-consumption semantics (linear-logic-flavored) by default.

**Every node gets an intensity.** Not an opt-in per corpus or per relation —
uniform across domain propositions, gate nodes, everything. There's no
`believed(p)` left to fall back to for the nodes that didn't opt in, because
nothing opts in; presence-as-a-separate-concept is gone, not narrowed.

**`-p` is gone as a sign; two RHS ops replace its one job.** `destroy($x)`
(unchanged, already shipped) removes a node's structure outright. Setting a
node's intensity to `0` — the general write, not a new named primitive —
switches it off while the node survives as structure. What used to be one
sign covering both readings is now two RHS operations with two different
costs, chosen explicitly rather than inferred from a `-`.

## What it turned out to cost

- **`keep` and `intensity` are the settled syntax.** `keep p($x)` is the
  antecedent read that does not spend; `+p(x) intensity $n` is the consequent
  write that names its own strength; `intensity($x) as $n` is the antecedent
  read of a bound node's current number.
- **Lanes went with the table.** Starvation was a fact about one selection per
  tick. `lane`/`lane_order`/`standing` stay reserved names so an old corpus
  still loads, but nothing reads them.
- **The focus system and frames went one step later.** Nothing scheduled by
  them once every matching rule fired, so they were bookkeeping with no
  reader. `attentioned($x)`'s job — *which one is in play* — is an ordinary
  claim a corpus writes and can argue with: `dungeon_gut.ugm`'s
  `eyeing(hero, $e)` is the worked case.
- **Calibration searches intensities now.** `numbers`/`mutate`
  (`ugm/learning/calibrate.py`) walked per-line scoring brackets, then
  `attend(...)` tails; both named a ranking that no longer happens.

## Triggers, and why gating had to move

Write-time triggers let a rule see another rule's pending conclusion as
`producing(<rule>, p)` and `drop` it or put something `instead`. They were
retired, and the corpora that used them — `tools_approval.ugm`,
`circuit_breaker.ugm`, `fs/fs_demo.ugm` — moved to gates.

**Consumption does not replace interception, and it is worth being exact
about why.** The obvious port is to make `<hold>` an ordinary rule that
consumes the dangerous occasion. It does not work: every rule whose
antecedent is on fires, so `<hold>` consuming `deploy(web)` does not stop an
`<execute>` rule that matched the same opening state. Both fire, and the
action happens anyway. That is measured in `triggers_are_retired()`, not
argued.

A gate is the replacement, and it is stronger than what it replaced. The
governed rule carries `keep gate(...)` in its own antecedent and cannot
conclude the action at all until something opens it — never minted, rather
than minted-and-rewritten — and the condition is visible in the rule it
governs instead of in a hook registered elsewhere. Swapping the policy still
never touches the governed rule: the gate line is the socket.

The one thing that got more expensive is WATCHING. `circuit_breaker.ugm`
counted a rule's activity by reading `producing(...)`, which cost the watched
rule nothing. It now counts `beat($tag)`, which the watched rule writes
itself — one line in the rule being watched, plus the `keep gate($tag)` the
breaker shuts to suspend it. In exchange the whole tainted-rule-reference
hazard disappears: there is no `<R>` in a fact any more, only ground tags.

## Known red

`todo.ugm`'s stack pointer races itself. `<push-task>` reads the current top
and writes the new one in one firing, and two tasks opened in the same tick
both read the same stale `$prev` — so the stack ends with two tops rather than
one stacked on the other. The table era's one-selection-per-tick serialised
this for free. A stack's push is inherently sequential and nothing about
order-independent firing can make two order-dependent writes to one pointer
agree; fixing it means restructuring `todo.ugm`, not patching the engine.
`todo_stack()` in `selftest.py` carries the failing check rather than a
green one.

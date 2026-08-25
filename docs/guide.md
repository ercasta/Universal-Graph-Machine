# Author's guide

What UGM is, the `.ugm` surface, and how to load and run a corpus. For the argument behind these
choices, read [the book](https://ercasta.github.io/Universal-Graph-Machine/). For what actually bites
once you sit down and write rules, see [`authoring.md`](authoring.md).

## The model

- **One graph is the whole state.** Nodes with ordered members, nothing else. `on(a, b)` is a node;
  `a` and `b` are nodes; an atom and a compound are the same kind of thing.
- **Belief is presence.** `believed(p)` holds or it doesn't — that's the entirety of "believing
  something" here. No confidence numbers, no provenance trail on a belief.
- **A member has one of three signs**: `+` (assert), `-` (erase), `no` (absence — *nothing claims
  this*). Belief is a flat set of occasions — asserting mints a proposition into it, erasing removes
  one. Asserting twice is two occasions, each with its own intensity.
  - `+`/`-` are **consequent-only**. A rule cannot use `-` as a premise — there is no "denied" entry
    left to match against; a premise can only ask *is this currently believed* (`+`) or *is nothing
    currently believed about it* (`no`). Writing `-p` in an antecedent is refused at load with a
    message pointing you at `no p` (nothing anchors it) or `+not(p)` (its denial is itself believed).
  - `no` in an antecedent matches when the proposition is not currently in the believed set — neither
    asserted nor its `not(...)` denial. This is the open-world trap: a state block that lists only
    what *is* true will not drive rules that ask what is *not*. Write your negatives, or derive them.
- **One connective.** `rule <name> = implies( { antecedent }, { consequent } )`. `causes` is refused
  at load — it only ever meant *lands in a later moment*, and there are no moments to land in.

## The loop

Each tick: score every rule, take the first whose antecedent matches against current belief, apply it
(write what it asserts, erase what it retracts), repeat. A run ends *quiescent* (nothing matches) or
hits a tick limit — `--limit N`, default 400. Nothing in the loop is privileged; stopping is a rule
spending a postcondition (`=> stop`), not an engine decision.

**Lanes** run more than one such pass per round. `fact +lane(<R>, watchdog)` puts a rule in its own
lane, guaranteed a turn every round regardless of what the default (`main`) lane selects that tick —
how a watchdog rule stays alive even when another rule always wins `main`'s arbitration. See
`ugm/rules/circuit_breaker.ugm`.

**Triggers** (`intercepts`/`producing`/`instead`/`drop`) let a rule see what another rule is about to
conclude, before it lands, and add beside it, replace it, or drop it:

```
fact +intercepts(<hold>, after)
rule <hold> = implies( { +producing(<request>, deploy($s)) },
                       { +instead(deploy($s), pending(deploy($s))) } )
```

This is the whole of how approval-gating and starvation-breaking are built — ordinary rules, no
engine hook per feature. See [`tools-approval.md`](tools-approval.md).

## Intensity, and what firing spends

Every node carries an intensity — a number. "On" is above zero, and that is the whole of what an
antecedent member and `no` ask about. What that means for a corpus:

- **A rule fires whenever its own antecedent is on.** Nothing ranks rules, nothing picks one per
  tick, nothing can starve anything. A tick matches every rule against the state as it stood at the
  tick's start, folds all their writes together, and commits once — so firing order cannot change
  the end state.
- **Firing SPENDS what it matched.** Every antecedent member a rule matched goes back to off unless
  something recharges it. This is why a guarded rule no longer has to be written to avoid
  re-deriving what it already derived.
- **`keep p($x)` opts one line out** — read without spending. Use it wherever a fact is meant to be
  read by more than one rule, or read again later: `delay.ugm`'s `owed($p, money)`, `todo.ugm`'s
  `task($t)` and `top(...)`.
- **A consequent can name its own strength**: `+p(x) intensity 3`. An antecedent reads the current
  number with `intensity($x) as $n`. Same-node writes in one tick combine by taking the max, so a
  rule's own consequent can outbid the discharge its own antecedent just requested — that is the
  runaway guard.
- **`ugm/rules/todo.ugm`** is the standing pattern for "keep something open until it's answered" — a
  task stack, closed by a `judge` rule a host corpus supplies. See [`todo-stack.md`](todo-stack.md).

See [`design/intensity-gates.md`](design/intensity-gates.md), and `python -m ugm.core.firing`
for the worked demonstration of each claim above.

## The surface

```
rule <cancel> = implies( { +cancelled($f) }, { +disrupted($f) } )
fact +cancelled(bl204)
say user: +checked_in(ana)
```

- **`rule <name> = implies({...}, {...})`** — braces, comma-separated members. There's also a line
  form with no braces or commas, one member per line, ending the antecedent with `->`:
  ```
  rule <cancel>
    +cancelled($f)
  ->
    +disrupted($f)
  ```
- **`fact`** deposits a member directly. A fact may be named (`fact <n> = ...`), sharing the same
  `<...>` namespace a rule's name lives in — names of *statements*, kept out of the relation
  namespace on purpose.
- **`say <channel>: +p`** delivers an arrival on a channel. Nothing is trusted by default — an
  ordinary trust rule turns an arrival into a belief.
- **`$x`** is a variable, scoped to the one statement it appears in. **`$p($x)`** — a variable in
  relation position — lets one rule apply an ability named by data rather than needing a rule per
  ability.
- **Postconditions** — a rule's own unconditional ops after its consequent: `=> stop`,
  `merge($a, $b)`, `unmerge($a, $b)`, `destroy($x)`, `label($x, name)`, `unlabel($x, name)`,
  `forget $x`.
- **`as`** binds what a member matched: `+on($x, $y) as $t`. Two members hoping to co-refer without
  it do **not** link.
- **`alias`** defines a corpus-local shorthand, expanded at load: `alias attacks($a, $t) = { ... }`.
- Numerals are ordinary atoms whose name reads as a number — nothing in the graph learns arithmetic
  except a reader that asks for it (a `kb.answerer` or `kb.computator`).

Uncertainty is an ordinary proposition (`+likely(p)`), never a grade attached to a member — the
parser refuses `@` syntax with a message pointing you here. Belief has no second time to bind, no
history, no derivation trail — one graph, one flat believed set, and no `why`/explanation mechanism
reconstructs how a belief got there.

## Tools and channels

`kb.answerer(name, request, fn)` binds a Python function to a relation; writing that relation calls
it, and its answer lands a tick later as `answered(<tool>, req, result)` — a record the corpus may
believe or not, never a conclusion the tool makes for it. `kb.computator(name, fn)` is the pure
variant: no graph access, runs during the match, so a multi-field update (a purse transfer) lands
atomically instead of being caught half-done.

## A rule is a node

`standing(<r>)` lifts a rule's priority so it isn't starved by an equally-ranked rival.
`dormant(<r>)`/`due(<r>)` suspend and resume a rule — ordinary facts a corpus writes, and a rule can
ask about, not a mark on the rule itself. There is no engine-level precedence relation — an exception
is written as a negated member inside the rule that should lose, not as a fact beside two competing
rules. See
[`authoring.md`](authoring.md) §2.

## Running it

```bash
python -m ugm ugm/rules/delay.ugm --ask "owed(ana,money)"
python -m ugm.selftest
```

`python -m ugm` loads one corpus, runs to quiescence or the tick limit, and prints what's believed,
newest first. There's no interactive loop or session save/resume in this repo — that's
[HarneSkills](https://github.com/ercasta/harneskills), a separate REPL built on top of this engine.

Verification is `python -m ugm.selftest` — one runner, not pytest, that prints every check's named
observation and counts any `False` as a failure.

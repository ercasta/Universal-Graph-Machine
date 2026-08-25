# Feature requests

Ideas scattered across the old `docs/` (deleted; see git history before this commit) that never got
built, or whose status was unclear. Kept here so they aren't lost. Not a roadmap — nothing here is
committed to.

Each item: what it is, where it came from, and whether it looked live or already resolved at the
time of extraction. Re-check against the current engine before acting on anything below — some of
these may since have shipped.

## Syntax

- **Rules/actions as facts.** `rule(name, implies(...))` so a rule definition is itself an ordinary
  fact a corpus can manipulate. (`todo.md`, `feature-request.md`)
- **Runtime-built LHS ("want" nodes) + `realize()`.** Mint a want node at runtime holding a
  requirement built from an RHS's own bound variables; `realize(g, node) -> Rule`, mirroring `reify`.
  (`feature-request.md`)
- **Episode-scoring triggers (ALWAYS/NEVER/WANT).** End-of-episode checks for learning/scoring;
  needs a wildcard absence member (`no p(*)`) that does not currently lex. Raised independently three
  times — the highest-value unbuilt item in this list. (`feature-request.md`, `wanting.md`,
  `review-notes.md`, `new_substrate.md`)
- **Scored RHS alternatives.** One LHS, several numbered RHS branches competing locally after the
  LHS wins the global table, each with its own weighted query members. `alt(...)` covers
  antecedent-branching but not this. (`feature-request.md`)
- **Global post-tick triggers.** A trigger with no host rule, evaluated every tick, installable and
  cancellable at runtime by an RHS. (`feature-request.md`)
- **`_` as a wildcard member argument** (`no subgoal(_, $w)`) — a hole that cannot bind. Proposed as
  a route to deleting `_root`; the bare `_` token currently traps silently. (`review-notes.md`)

## World model

- **Dimensions/positions as first-class** (time, size, etc. as comparable positions), and a formal
  query vocabulary (`List`/`Bag`/`Set`/`All`/`Some`/`count`/`greater`/`smaller`) beyond what `count`
  already gives. (`new_substrate.md`, `world-model.md`)
- **Fuzzy/gradable queries** — e.g. "old man" as a degree function weighting rule applicability
  rather than gating it binary. Flagged as risky: conflates truth-degree with relevance-degree.
  Proposed split: degree-of-truth is a corpus claim, degree-of-relevance is a chooser weight.
  (`review-notes.md`)
- **Composable "world models" for context-dependent legality** — no hardcoded forbidden/invalid in
  the engine; each context (imagining, playing casually, a real tournament) is its own model, with
  "bridge concepts" composing a core model with an outer one. Philosophical, unresolved.
  (`review-notes.md`)
- **Rule bodies as a reversible AST** so rules can read and rewrite other rules' bodies, plus
  automatic `x causes y` ⟹ `want y -> want x` inference. Speculative, low elaboration.
  (`rules round trip.md`)

## Multi-agent

- **Cross-agent shared time reference** — an agent cannot currently utter or refer to a specific
  moment (every moment renders identically), so two agents can't agree on "you moved before I did."
  Flagged independently twice as a real ceiling. (`table-design.md`, `dungeon-reply.md`)
- **Teaching another agent a rule** (not just ground facts) — a fact may not contain a variable, so
  this is presently unclear whether it's a deliberate limit or a gap. (`table-design.md`)
- **A dispatched-marker for `m.emitted`** so an integrator doesn't need to track its own read cursor
  over the cumulative act list. Minor convenience. (`table-design.md`)
- **Silence over an unnamed channel** — negation-as-failure over "nobody said anything to anyone" (as
  opposed to "on channel X," which works today). Not requested formally; open if a corpus needs it.
  (`dungeon-reply.md`, `authoring.md`)

## Diagnostics

- **Static self-loop detector** — extend `ugm.atlas`'s "pairs that could disagree" analysis to flag a
  rule whose consequent can restore its own antecedent. (`quest-feedback.md`)
- **Runtime rhythm/loop detection** — detect a repeating `(seat, rule, bindings)` sequence at period 1
  (measured as a perfect discriminator) and deposit `circling(<seat>)`, without stopping the loop
  itself. Designed and measured, deliberately left unbuilt pending a second falsifying (2-cycle)
  fixture. (`rules-design.md` Appendix A, `HANDOFF.md`)
- **Reasoner calibration** — no held-out set or measured failure rate for the reasoning engine, unlike
  a classifier. (`observations.md`)
- **Scoped/local widening record** — a way to say "this line of work found nothing" distinct from
  "the whole machine found nothing," for graceful-degradation use cases. Confirmed not built; repair
  tiers are reached, only the record is missing. (`interpretation-feedback.md`, `interpretation-reply.md`)
- **Floor-tier repair rules starving under busy agents** — a floor-priority repair rule only runs once
  every higher-tier rule is exhausted, so it fires only after the room goes quiet. Open defect, not a
  request. (`interpretation-reply.md`)
- **"Cheapest derivation" quantification** — cost-summing across a derivation, for parser-style repair
  ranking. `count`/`counted` cover the other three faces (negative existential, universal-over-stretch,
  uniqueness); this one remains unaddressed. (`interpretation-feedback.md`, `observations.md`)

## Learning

- **Calibration policy for the numbers a corpus carries** — the mechanism is built
  (`numbers`/`mutate` walk `intensity` writes, `run_episode` scores them), but no corpus-side policy
  reads a reward signal and revises those numbers; credit assignment is left open. Raised in three
  sources, back when the numbers were attention weights. (`HANDOFF.md`, `feature-request.md`,
  `observations.md`)
- **Goal-as-commitment vs. goal-as-belief** — retiring a goal on pursuit (rather than leaving it
  standing) works with no engine change but breaks credit-tracking and commits before success is
  known. Measured, two known interaction bugs, not merged. (`HANDOFF.md`)
- **Subgoal splitting for learning/blame** — splitting an episode into subgoals so a failed subgoal
  (not the whole episode) can be blamed on a specific rule. Partially explored; final state unclear.
  (`HANDOFF.md`)

## Design's own open-questions list

`rules-design.md` §22 — self-flagged as stale even at the time; re-verify each before acting.

- Magnitude-of-cost for rule failure (`harmed` is boolean today).
- Forgoing's remaining edges: a later-applicable rival isn't noticed until the tick the choice is
  made; "these two rules should both run" has no declarative vocabulary beyond denying the deposit.
- Goal "discharge" as a first-class notion (achieved/refused/handed-over/abandoned).
- Wind-down after stopping — nothing can key on `stopped` for a non-goal-triggered wind-down.
- Multi-episode learning — experience is one episode deep.
- A familiarity measure ("have I seen moments like this?"), distinct from "did recall return anything."
- Exploration schedule/rate — when an exhaustive recall pass should fire absent an impasse.
- Retracting a contradicted expectation — precedence stops a defeated rule applying but doesn't
  retract what it already concluded.
- Backtracking: who decides to reconsider a binding (currently keyed on `quiet`) is unresolved.
- Span normalisation by chain order rather than member order — unspecified.
- Calendar-term resolution — who computes it, against whose clock.
- Arrival-as-moment representation — unresolved.
- Criterion for crossing a modality ("when to suppose") — proposed criterion is demand (backward
  reading), not yet connected.
- Vocabulary for incompatibility — can deny a proposition, can't say two distinct propositions are
  mutually exclusive. A `refutes` relation existed in an older engine and didn't survive the restart.
- Statically enforcing the write-gate property ("no write bypasses the stamp") — true by placement,
  no checker.

## Already resolved (kept for the record, not for action)

These looked done, or done-adjacent, at extraction time — spot-check before re-requesting:

- `bounded(<ticks>)` on hitting the tick limit — shipped.
- The tool/action approval-gating pattern (`<hold>`/`<approved>`/`<denied>`) — shipped as
  `ugm/rules/tools_approval.ugm` and `ugm.probes.tools`.
- `watch` callback receiving the `Step`, and a caller-supplied `Table` across `run()` calls — shipped.
- `prefer`/buff unification for offline learning — shipped.
- Scan-cost reporting by size, not just count — shipped.
- An interactive REPL with session save/resume — built, but in the sibling **HarneSkills** repo, not
  here.

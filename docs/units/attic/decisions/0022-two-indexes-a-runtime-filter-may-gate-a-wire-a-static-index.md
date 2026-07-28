# 0022. Two indexes: a runtime filter may gate a wire, a static index may not

**Status — current (2026-07-28): HISTORICAL.** predates the substrate inversion (2026-07-26). Not contradicted by name in `../../model.md`, and not carried forward as current either — read it as context, not as a decision in force.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §19, §24.7, §28; `bench/spike_computed_index.py`

## Context

The index keyed on the predicate alone. On a two-line rule that is already wrong: a rule concluding
`socrates is_a mortal` looks like a producer for a pattern reading `?x is_a man`, so the assembler spawned an
instance that could never fire. Since patterns come from forms, which pattern can feed which ought to be
computable rather than accumulated.

## Decision

**Two indexes, and conflating them would be unsound.**

| | over | may gate a wire? |
|---|---|---|
| runtime filter | **facts vs atoms** — can any fact here satisfy any atom of this pattern? | **yes**, exact |
| static index | **templates vs templates**, a pure function of the library | **no** |

The static index's job is **diagnosis**, not dispatch.

## Evidence

- **Why the static index may not gate:** a `given`, a `branch` and a carrier are units whose output
  no template describes. Gate on the template relation and every hand-supplied fact is cut off from the rules
  that read it.
- **The filter must span both polarities.** A producer whose only relevant fact matches a *negated* atom cannot
  justify a firing but can *suppress* one, so refusing that wire changes the answer.
- **Payoff is shape-dependent.** On a `next`/`reaches` chain: nothing, ~3% overhead — those predicates were
  already selective. On a taxonomy where every template reads and writes one predicate: instances `2k-1` → `k`,
  and budget spend **quadratic → linear** (265 → 23 at k=12), because a dead instance is itself a producer and
  spawns more dead instances.
- **That shape is the one a minimum form set has**, which was predicted in advance as a tension: with ten forms
  all discrimination falls on predicate constants.
- **`Net.index_audit()` is the gate**, written as a differential against consumed premises rather than against
  the filter's own decisions — asking a filter whether it agrees with itself measures nothing.

## Consequences

- `ComputedIndex.wildcards()` names unselective patterns from the form set alone, before a unit
  exists. That diagnosis is the real payoff; the speedup is shape-dependent.
- **No static analysis can restrict a trace consumer** (measured selectivity 0.0): its atoms are all-variable
  except their predicates, and no shape says which units it grades. A content-level restriction is available and
  unbuilt.
- A refusal is recorded in the journal as `<no_shape_match>` rather than being silent.

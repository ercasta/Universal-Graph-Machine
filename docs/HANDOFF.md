# Handoff — 2026-08-25 (attention, focus and frames removed)

    python -m ugm.selftest          184 checks, 1 failing  (known red, below)
    python -m ugm.gates.vocabulary   16 checks, 2 failing  (known false positive, below)
    python -m ugm.core.firing        every worked example held
    python -m ugm.probes.tools        0 failing
    python -m ugm.probes.autocorrect  0 failing
    python -m ugm.probes.dungeon_micro  0 mismatches / 14 seeds
    python -m ugm.probes.dungeon_gut    0/30 divergence

Both failures are unchanged from before this session — measured against `main`, not assumed.

## What went

Intensity superseded attention and focus, so all three layers are now gone rather than kept beside
each other:

- **The focus pool** — `Machine._attend`/`_attended`/`_attend_written`/`_push_attention`/
  `_fade_attention`/`_unattend`/`_consume`, the `ATTENTION_*` constants, `_lane_state`,
  `_evicted`/`_readmitted`/`_fresh_attention`.
- **Frames** — the `Frame` class and its standing weights, `_frames`, `_floor`, `_push_frame`,
  `_pop_frame`, `_declined_frame`, `FRAME_DEPTH`.
- **The surface** — `attend(...)`, `brush(...)`, `unattend`, `push(...)`, `pop(...)` as
  postconditions, and `attentioned($x)` as a predicate. All five postconditions are now a
  `ParseError`, not a silent no-op; `focus_is_retired()` in `selftest.py` checks exactly that.
- **The reserved names** — `attention`, `attention_span`, `frame_depth`, `pushed`, `popped`,
  `declined`, `unattended`, `attentioned`.

**None of it was load-bearing by the time it was removed.** The intensity commits had already taken
away the thing focus fed: nothing ranks rules, nothing picks one per tick, so the pool had no reader.
The removal is subtraction, not a rewrite — which is why the probes produce byte-identical output.

## The one real port: `attentioned($x)`

`dungeon_gut.ugm` was the only corpus using it as a live gate — `<hero-targets-threat>` fired only
when the reflex layer had attended the enemy. That became `keep eyeing(hero, $e)`: the ordinary
claim `<eye-the-threat>` already deposited alongside the `attend($e, 5)`. A corpus asking "which one
is in play" now reads a claim it owns and can argue with, rather than the engine's scheduling state.

Everything else was already vestigial and its comments said so.

## Calibration searches intensities now

`numbers`/`mutate` (`ugm/learning/calibrate.py`) walked per-line scoring brackets, then `attend(...)`
tails. Both named a ranking that no longer happens, and the selftest check over them had gone
vacuously green — `numbers()` returned `[]` for both corpus and mutant, so
`len(numbers(c)) == len(numbers(corpus))` held for free. They now walk `intensity <n>` writes, which
is the number a corpus actually carries, and `calibration()` checks that a mutant still parses and
that no intensity is nudged below zero.

## `ugm/core/attention.py` → `ugm/core/firing.py`

The file has held the tick loop and nothing else since the intensity commits. `machine.py`'s two
deferred imports, `core/__init__.py`'s layering note, README, `docs/guide.md` and two book chapters
were updated with it.

## Known red, both pre-existing

- **`todo.ugm`'s stack pointer races itself.** `<push-task>` is a read-modify-write on
  `top(internal_todo, $t)` and two tasks opened in one tick both read the same stale `$prev`. The
  table era's one-selection-per-tick serialised this for free. Fixing it means restructuring
  `todo.ugm`, not patching the engine — see the comment on the failing check.
- **`ugm.gates.vocabulary`'s two web failures** are the generic `+$p` trust rule: the consequent is a
  bare variable, so the static scanner cannot see that `<trust>` writes `cancelled`/`heat`/etc. Real
  at load time, cosmetic in the diagnostic.

## Not done, deliberately

`book/docs/` still describes the ranked table, the focus queue and push/pop frames as live features —
ch. 25, 27, 28, 29, 30, 32 and the appendix, ~1600 lines. That staleness arrived with the intensity
commits, before this session. `docs/design/intensity-gates.md` now carries a pointer at the top
saying so; porting the book is its own pass.

## Worth knowing

- **`todo_stack()`'s "closed task is unpinned" check was passing vacuously.** It looked up
  `task($t)` PROPOSITIONS in the focus pool where the keys were `$t` NODES, so every lookup missed
  and the `all(...)` held for free. Its replacement asks about `retired($t)` and resolves member 0.
- **`_by_key`/`_by_arg` still never shrink on erasure** (carried over unchanged, third handoff).

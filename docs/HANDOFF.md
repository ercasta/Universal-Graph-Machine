# Handoff — 2026-08-25 (green)

    python -m ugm.selftest         198 checks, 0 failing
    python -m ugm.gates.vocabulary  16 checks, 0 failing
    python -m ugm.probes.tools       0 failing

Green for the first time since the token migration started.

## A correction to the last handoff

It claimed the approval corpus had started working. It had not. `<hold>` was
not intercepting at all, so `deploy(web)` was written unapproved and three
checks passed **vacuously** — nothing was pending, so nothing was left
pending. That was a regression from the interning commit, not a fix.

`_obey` keyed its instructions on node identity. `instead(deploy($s),
pending(deploy($s)))` is a pattern the trigger grounds, so the `deploy(web)`
inside it is a node built to say *which* conclusion — never the conclusion
node, which the intercepted rule built. Those were one node while `rel`
interned. Instructions are keyed by shape now, and the `tools` probe went from
2 failing to 0.

## What the remaining failures turned out to be

Almost none of them were about interning, and almost none needed engine
changes. Four kinds:

**An answer carried no token.** `_answer` called `_attend_written` on the
answer with a comment saying exactly why it must — and `_attend_written`
skipped it, because `answered` was on the `_bookkeeping` list. One list was
answering two questions: *is this part of the world* (`_contents` wants no)
and *is this worth thinking about* (an answer is new business, so yes). Split
into `_bookkeeping` and `_incidental`.

This is also what had `dungeon_gut` reporting 0/30 divergence — its judge and
reflex rules were dead. It reports 10/30 now, which its own docstring calls
the interesting result rather than a bug.

**Corpora written before tokens.** A move spends what it matched on, so a
premise two rules both need is gone after the first one runs. `delay.ugm`
never asked about compensation because `<care>` ate the disruption; one
`brush` on `<care>` fixes the corpus and the vocabulary gate with it. Same
shape in two fixtures:

- arbitration's "a loser is deferred, not rejected" — true of arbitration,
  and now separable from consumption. The check says so.
- the circuit breaker's `<flaky>`, which was supposed to be a rule that never
  stops matching and instead stopped after two firings. A watchdog watching a
  rule that stops on its own is watching nothing.

**Fixtures that could not test their own claim.** `attentioned($x)` attended
an atom on a machine whose pool still held everything the load wrote, so the
predicate opened for everybody. It needs an empty pool, the occasion (which
the line has to match on) and the referent (which the predicate asks about) —
three separate things that were one while a token sat on anything.

**A constant that had drifted from its docstring.** `ATTENTION_BRUSH` read 5
against a comment saying *one tick, and then it is somebody else's turn*. Back
to 1. It costs nothing now; when it was tried earlier in the session it looked
like it broke `dungeon_gut`, and that was the answer-token change being
misattributed.

## Worth knowing

- **`_by_key` and `_by_arg` never shrink on erasure**, only on `delete`. Not
  visible at this size (largest bucket on `worked.ugm`: 2).
- **`Gate.erase` picks the OLDEST occasion** when handed a shape rather than a
  node. A ground `-p(a)` has no binding to carry an occasion, so something had
  to give — but it is the engine making a choice, which it does not usually do.
- **`attention.py`'s spend path still builds** — `_ground` and the after-query
  probe substitute patterns into fresh nodes. Correct, since they are matched
  structurally, but they leave nodes behind.
- **`brush` has no corpus using it outside fixtures and `delay.ugm`.** Any
  corpus where two rules share a premise needs one, and the failure mode is
  silent: the second rule simply never runs.
- The `dungeon` probe now ends with `hp(hero, 0)` rather than 12. Same
  verdict (`UNRESOLVED`), more of the fight actually happening.

# Handoff — 2026-08-25 (never intern)

    python -m ugm.selftest    198 checks, 10 failing

Still red, and the same red. Measured against the previous commit with its
crash guarded (see below), the baseline was **193 checks, 13 failing**. Three
of those thirteen now pass and none of the ten is new.

## What went

`Graph.rel` interned; it does not. A relation instance is a distinct node
every time it is built, and `instance` is gone because it had become the same
function.

- `p(a)` said twice is **two occasions**, each with its own anchor and its own
  attention token. That is the point: attention is spent per occasion, and
  occasions cannot be distinct while structure is identity.
- What is one node and what is one proposition came apart. `_by_key` indexes
  every node by its **shape** — structural, all the way down, because a member
  id stopped being its own shape the moment nesting could be rebuilt.
- `merge` stopped re-keying. It is a dict write and the labels; congruence
  moved to the read side, where `counts_as` widens a lookup to the class and
  `unify` compares through `identity_of`. No cascade, so `unmerge` has nothing
  to refuse but a non-top claim. `_key`, `_keyed`, `_mentions`,
  `_merge_indexed`, `_index_for_merge` and `_merges` are all gone.

Three of the four faces of the old interning bug came from **building a node
in order to ask about one**. Nothing does that any more:

- `Machine._claims(rel, *members)` and `_note_that(rel, *members)` take the
  parts and look up; they never mint to ask.
- An `absent` member and a `-` consequent both resolve through `already_there`
  — which was dead code and is now the load-bearing question.
- `Application.matched` carries the node each antecedent line bound. It is
  back because nothing else can reconstruct it: rebuilding with `substitute`
  used to hand back the very node matched and now mints a stranger. Attention
  reads it, and attention deciding what a move spends is the whole token line.
- `Scratchpad.occasion(p)` is where a caller holding a *shape* meets an engine
  holding *occasions* — `Gate.erase` and `Machine._attend` both go through it.

Cost, on `worked.ugm`: 195 nodes against 194, same ticks, same quiescence,
same beliefs. Suite runtime unchanged.

## Surface change

`fact +p(a)` twice now believes it twice. `docs/guide.md` and four book
chapters said the opposite and were rewritten.

## The two token bugs

Both named in the last handoff, both fixed by this, neither aimed at:

- a tool's answer landing **no token** — the approval corpus reaches
  quiescence and consumes its pending record now.
- `_attend_written` re-attending what a move **erased** — the erase path no
  longer manufactures the node it is erasing.

The `denied` half of approval is still red.

## Still failing (10)

Seven were failing before this line started: arbitration's deferred loser,
`denied` reaching quiescence, the attention claim surviving its own move,
`attentioned($x)` picking paul out, `forget $hit` in both spellings, and the
circuit breaker tripping more than once.

Three more were never *reached* before: the runner died on an `IndexError` in
`circuit_breaker` — a red check's own fallout — and took every section after
it down. It reports rather than raises now, which is what makes the 193/198
comparison possible at all. The two entitlements failures behind it match
`ugm/gates/vocabulary.py`, which fails the same two against the old commit.

## Next

- **`_by_key` and `_by_arg` never shrink on erasure** — only on `delete`. A
  long run accumulates spent occasions in the buckets the matcher walks. Not
  visible at this size (largest bucket on `worked.ugm`: 2) and it is the
  obvious first place to look when it is.
- **`Gate.erase` picks the OLDEST occasion** when handed a shape rather than a
  node. That is a choice the engine makes, and this repo does not usually make
  choices. A ground `-p(a)` has no binding to carry an occasion, so something
  had to give; worth revisiting rather than inheriting.
- **`attention.py`'s spend path still builds** — `_ground` and the after-query
  probe substitute patterns into fresh nodes. Correct, because they are
  matched structurally, but they leave nodes behind.
- The remaining seven failures, which the token line owns.

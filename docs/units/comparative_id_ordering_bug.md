# Finding + FIX: `min(same-named-nodes)` breaks once ids cross a power-of-ten boundary

**Written 2026-07-30, found while verifying the book's live playground against `grammar`'s test suite
regressions (`docs/units/scope_visibility_blocks_forks.md`, `atms_env_across_forks_gap.md`).**

## The bug

`book/docs/playground/uncertain.md` (and `tests/test_world.py::test_suspicion_is_a_partial_order`)
promote asking `is cy more suspicious than bo` — the book says it's "worked out through ada" (transitive:
`cy > ada`, `ada > bo` are both declared, `cy > bo` should follow). It returned `unknown` instead.

Root cause, unrelated to today's other fixes: `ugm.cnl.comparative._entity` (and two siblings,
`chain._index_entity`, `possibility._entity`) pick the canonical node for a repeated name via
`min(g.nodes_named(name))` — a **string** comparison over node ids of the form `"n<int>"`. That breaks
once ids cross a power-of-ten boundary: `"n114" < "n42"` lexicographically (`'1' < '4'` at the second
character), even though `114 > 42` numerically. Verified directly: by the time `cy is more suspicious
than ada` was authored, `cy` already had three nodes (`n42` the true base, `n91`/`n114` fork-scoped
copies from earlier hedge/either-or lines in the same corpus) — `min()` picked `n114` (a fork-scoped
reference) instead of `n42` (base), so the comparative fact attached to a node ordinary base-vantage reads
can never find. This has nothing to do with the `_pencil`->`_relativize` migration or possibilistic
scoping specifically — it's a plain, pre-existing id-comparison bug that any sufficiently large corpus
(enough nodes minted before the affected name's later mention) could trigger.

## The fix

All three call sites changed from `min(found)` to `min(found, key=lambda n: int(n[1:]))` — tie-break by
the numeric id (the actual mint order), not the string. `ugm/cnl/comparative.py:_entity`,
`ugm/chain.py:_index_entity`, `ugm/possibility.py:_entity`.

## Verified

- `tests/test_world.py::test_suspicion_is_a_partial_order` — now passes.
- The book's `playground/uncertain.md` promoted interactions, re-run against the fixed engine:
  `is cy more suspicious than bo` → `yes` (was `unknown`); `why is cy more suspicious than bo` → the
  two-step declared chain (`cy > ada`, `ada > bo`); `is cy more suspicious than dan` → `unknown` (honest
  incomparability, unchanged, correct). Every other promoted interaction (`who is thief`, `is cy thief`,
  `is ada thief`, `guess culprit`, `why cy is thief`) verified to match the book's documented output
  exactly, character for character.
- No new failures introduced (`tests/test_world.py`, `test_comparative.py`, and the four
  `test_possibility_*.py` files re-run clean alongside this fix).

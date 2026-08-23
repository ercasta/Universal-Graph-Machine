# Feature request

Checked against the current engine (`ugm/core/rules.py`, `ugm/core/attention.py`,
`ugm/core/machine.py`) on 2026-08-23. `docs/rules-design.md` is outdated and was not
consulted for this pass.

## 1+2. "want" as a runtime-built LHS, and running it

Single want node, created at runtime by an RHS, holding a requirement built from that
RHS's own bound variables (a closure) -- e.g. checking that one particular Hanoi tower,
among several in the graph, has reached a specific configuration. The pain point is not
being able to author ad-hoc, data-shaped requirements without writing a KB rule per case,
which does not generalize.

Merged with item 2 ("allow the RHS to run the code in a node"): the concrete want is a
function that turns a subgraph expressing an LHS into an actually runnable LHS. Not
`eval`, not arbitrary code -- reuses machinery that already exists in two halves:

- `Machine.reify` (`machine.py:430`) already writes a rule's antecedent out as graph
  facts, `+ant(<node>, pattern, mode, i)` -- one-way, Rule to facts, built for R4
  askability. What's missing is only the reverse read.
- `_spend_posts` (`attention.py:690`) already does the reverse trick, in miniature: it
  builds a throwaway `Rule` from a `List[Member]`, substitutes an application's bindings
  into it, and calls `match()` -- the same interpreter every ordinary rule uses, no
  eval, no purity violation.

Design: an RHS writes the want's requirements as ordinary `+ant($w, on(disk3,pegC),
assert, 1)` facts (its own bound values -- the closure, for free). A new function
`realize(g, node) -> Rule` mirrors `reify`, reading `ant`/`con` facts back into a
`List[Member]`. Exposed to corpora as a **predicate** (not a computator -- computators
are pure and cannot touch state; predicates already exist for exactly this: read state,
answer bool, bind nothing, cf. `attentioned($x)`): `satisfied($w)` realizes `$w`'s
antecedent and calls `match()`, answering whether it found at least one application.
Episode/goal checks become ordinary rules, no per-configuration authoring:

    { +want($w), satisfied($w) } ⟹ { +reached($w) }

## 3. Triggers for learning: ALWAYS, NEVER, WANT

End-of-tick/episode check: is some LHS-like condition always true, never true, or was a
"want" reached -- for scoring an episode's success.

WANT is already free: exactly the dungeon's `<victory>` shape, `no ... ⟹ +over(...)`,
and composes directly with item 1's `satisfied($w)` once that exists. ALWAYS/NEVER want
a wildcard absence member (`no p(*)`) that is still unbuilt -- `wanting.md` §9's own
design, independently wanted twice already (the judger stress test, and this). Nothing
today distinguishes a check *for scoring/learning* from an ordinary domain conclusion;
that's the open half. This is the same destination as the calibration item already
flagged at the bottom of `HANDOFF.md` (2026-08-23): the mechanism (`Frame.weights` →
`_pull` → per-rule lift → `Table.order`) is built, the corpus-side policy that reads a
feedback signal and revises `attend(...)` is not.

## 4. Rule alternatives: one LHS, several scored RHS branches

One rule represents both world model (the LHS) and agent style (which numbered RHS
alternative it prefers, and when).

Two-tier, and this is the key correction from the first pass: the LHS as a whole
competes in the **global** table exactly as today, unchanged -- one `Rule` node, one
score, ordinary `arbitrate`. Only once that rule has already won the tick does a
**second, local** competition run among its numbered RHS branches, using that
application's own bindings, and it never touches `Table`/`_pull`/`by_relation` at all.
(First pass wrongly tried to make branches compete globally via attention's `_pull`,
which is keyed by relation and can't tell two branches sharing one LHS apart -- wrong
layer entirely.)

Local competition reuses the same primitive as items 1+2: each branch carries its own
extra query members (the "LHS scoring conditions"), each with an authored weight. At
apply time, substitute the winning application's bindings into each branch's queries,
run them through `match()` (same call `_spend_posts` already makes), sum the weights of
whichever queries matched per branch, argmax, ties break by authored branch order
(mirrors `arbitrate`'s own final tiebreak). Substitute and apply only the winning
branch's consequent. The weight is an ordinary authored fact -- `bonus(<rule>, 2,
<condition>, n)` -- never a mark on the rule, so it's learnable/revisable the same way
any other claim is, no new acquisition machinery needed.

`alt(...)` today only varies the *antecedent*, compiled into N separate Rules at load,
each competing globally -- the mirror-image case, and it does not solve this on its own,
though its "compile at load, never a runtime branch" discipline is not reusable here
either, since branch selection must stay local to the one already-chosen application.

## 5. RHS installs triggers, global, running after every tick

Not the existing `after <R> { query } ⟹ ...` statement (now foldable into a rule's own
RHS tail) -- that trigger is scoped to one host rule's own application, evaluated only
when that specific rule wins a tick. This is a trigger with no host rule, evaluated
every tick regardless of which rule (if any) won, and installable by an RHS at runtime
rather than authored at load. RHS's tail can also cancel it.

Old `after` statement is an unused deletion candidate (`HANDOFF.md`: "no shipped corpus
and no selftest check uses a live `after`/spend trigger anywhere"), so extending the
trigger machinery is cheap, not a fight with something load-bearing.

`RuleSet.triggers` (`rules.py:311`) reserves the `None` key in a comment for a
*different*, still-unbuilt future purpose ("what to reach for at ranking time") -- a
global post-tick trigger needs its own key/list, not that one.

## Suggested build order

Extract `_spend_posts`'s "substitute bindings into a query, build a throwaway `Rule`,
call `match()`" into a standalone helper first (pure refactor, should be a no-op on the
suite) -- items 1, 2, 4's local half, and the existing `after` trigger all become
callers of the same function. Then `realize`/`satisfied($w)` (unlocks Hanoi-shaped
wants). Then branch scoring. Then the wildcard absence member for item 3's ALWAYS/NEVER.
Item 5 is independent of this thread and can be picked up separately.

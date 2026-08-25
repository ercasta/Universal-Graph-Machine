# Handoff — 2026-08-25 (todo stack + decay restored)

    python -m ugm.selftest         203 checks, 0 failing
    python -m ugm.gates.vocabulary  16 checks, 0 failing
    python -m ugm.probes.tools       0 failing

Green. Two asks, and the second turned out to depend on fixing the first properly rather than just
flipping a switch: restore attention decay, and build a standing todo/task-stack mechanism
(`internal_todo`, tasks as a stack, a `brush` lane, a `judge` lane, "arrival becomes an open task").

## Decay was dead code, and turning it on was not a one-line change

`_fade_attention` (`Machine`) was fully built and unit-tested but never called from the tick loop
(`attention.run`) — nothing decayed, ever, in any real run. Wiring in one `m._fade_attention()` call
per tick surfaced two real, independent gaps, both fixed at the engine level:

- **A deposited doubt carried no attention token.** `close(...)` was on `_bookkeeping`/`_incidental`,
  so `<settle-doubt>` (or a corpus's own settling rule) could never survive `_attended_first`'s filter,
  however high the table ranked it. Invisible while nothing ever decayed — whatever was already
  attended kept overlapping by accident. Fixed: `close` now attended like `answered` already was
  (`_incidental = _bookkeeping - {ANSWERED, CLOSE}`), and the doubt branch in `attention.run` calls
  `_attend_written` on what it deposited.
- **A rule matched against several ground things at once only ever got the FIRST — the rest were
  silently dropped, never even entering the doubt mechanism** (that only fires between *different*
  rules tied in one window; the shortlist walk takes `found[0]` per rule and discards `found[1:]`
  outright). Under decay, a sibling held at brush strength has exactly one tick to be picked, and the
  loop only picks one application per lane per tick — so the second `say` in a corpus, or the second
  ground instance a rule matches at once, lost its only turn. Fixed: both the doubt branch and the
  shortlist's own `found[1:]` now **revisit** every unpicked match's matched nodes
  (`m._push_attention(node)`, no explicit weight) rather than leaving them to decay unseen.

**The revisit, not a brush.** First attempt used `m._attend(node, weight=ATTENTION_BRUSH)` for both of
the above — which *stomps* a node already held stronger (an arrival, now at `ATTENTION_START`) down to
1, undoing the very durability that was supposed to protect it. `_push_attention(node)` with no start
is the correct primitive: it restores whatever the node already had, or falls back to brush strength
only if it never held anything. Two arrivals landing in one batch is the fixture that caught this —
the second was opened as a task fine, but its own weight-5 got downgraded to 1 by the first fix's own
sibling-brush, one tick before its turn came.

## Loaded facts get NO attention — a deliberate choice, not a bug

Corrected mid-session, from the user directly: a `fact` is background, not something to take care of.
Attending is *taking care of something*, and that comes from a channel by default now, not from being
loaded. This is a bigger change than it sounds — `_attended_first` has **no exception for an empty
pool** ("attending to nothing means there is nothing for work to be about, and the computation is
meant to fade out"), so a corpus with no `say` and no explicit `attend(...)` now does nothing at all,
ever. That broke roughly 40 of 198 selftest checks and every shipped corpus with a purely
`fact`-driven start. Retrofitted, not worked around:

- **`ugm/core/text.py`**: `Loader._state` no longer calls `_attend_written` on a loaded `fact`.
- **`ugm/core/machine.py`**: a channel arrival now attends at `ATTENTION_START` (5), not a brush's 1 —
  arrivals are the primary source of "take care of this" now, and one tick was not enough runway to
  survive being the second of several delivered together.
- **`delay.ugm`, `tools_approval.ugm`**: the triggering facts became `say` arrivals plus a small
  generic `<trust>` rule (`+says($ch,$p), no trusted($ch,$p) -> +trusted($ch,$p), +$p`) — a disruption
  or a want is news, not eternal background. Guard on a dedicated `trusted(...)` marker, **never on
  `$p` itself**: guarding on `$p`'s own absence breaks the moment downstream business logic erases
  `$p` (`<request>`'s `-want(deploy($s))`), since absence then holds again and re-triggers.
- **`delay.ugm` needed several MORE hops of the same fix**, because it is BUSY — `<care>`, then
  `<compensate>`, each consume `disrupted($f)`/`booked($p,$f)` before `<reroute>` gets a look. Each
  consuming rule got `after <R> { $x = p(...) } => attend($x, 5, 1, 1)`. The corpus's OWN existing
  `brush(disrupted($f))` on `<care>`'s tail turned out to be a **latent no-op**: `$f` is an argument,
  not the whole matched line, so the tail rebuilds `disrupted($f)` by substitution and mints a twin
  (`rel` does not intern) rather than re-attending the real node. `after <R> {query} => attend(...)`
  is the one that actually works, because the query is a MATCH against belief, never a rebuild.
- **`worked.ugm`, `circuit_breaker()`'s and `calibration()`'s own selftest fixtures**: kept textually
  as printed/original where that mattered (the design document, an episode file's own "nothing else is
  needed to run it" claim), with the kickoff added on the Python side instead
  (`m._attend(kb.term(...))`, same idiom `circuit_breaker()` already used before this session).
- Roughly 30 more selftest fixtures needed the same one-line `m._attend(...)` addition — mechanical,
  not interesting; see the diff.
- **Cost not chased further**: `ugm.probes.dungeon_gut` no longer shows the 10/30 divergence its own
  header describes — 0/30 now, though the reflex layer does still fire (11/30 "eyeing" without
  fleeing). Outside `python -m ugm.selftest`'s mandate; the fights still resolve/UNRESOLVE the same as
  before, nothing crashes, but the exact statistical profile shifted with the new attention pace and
  was not re-tuned.

## `ugm/rules/todo.ugm` — the actual ask

A standing corpus, loaded alongside a host corpus with the **same `scope=`** (`tools_approval.ugm`'s
own discipline). Not in `bundle.ugm` — asked and answered directly: the bundle is deliberately one
reading-only rule (`the_bundle()`'s own test says so), and task management is policy, the same
standing that already emptied the bundle of everything but `<intake>`.

- `internal_todo`: pinned (`floor=1`) the moment the file loads, via its OWN arrival
  (`say todo: +boot`) — not contingent on the host corpus ever saying anything.
- `<open-task>`: any arrival on any channel (except the file's own `todo` bootstrap channel, excluded
  structurally via `no internal($channel)`) opens a task. Generic over the relation — `+task($t)` is
  the whole contract, so a corpus's own rule can open one too.
- A stack, one pointer (`top(internal_todo, $t)`), self-based on the sentinel
  `top(internal_todo, internal_todo)` — pushing the first task and popping the last are the same code
  as every push/pop between them.
- `<brush-top-task>`, alone in its own `brush` lane: re-attends its own two matched lines every round,
  which is what lets one application keep surviving `_attended_first` tick after tick instead of being
  consumed once and never seen again — the actual mechanism behind "repetition doesn't lose the task."
- `judge` lane reserved, no rule of its own in it — closing a task (`completed($t)`) is the host
  corpus's business, same reasoning as the bundle's own emptiness.
- **`<open-task>` needed its own lane**, separate from the other stack bookkeeping (`push-task`,
  `notice-new-task`, etc.) — `SHORTLIST` (`core/attention.py`) only walks 5 candidates per cut before
  the outer widen loop stops if something already matched, and a 6th-ranked rule on a busy tick is
  never tried at all that tick. Two arrivals landing together had the second lose its only turn,
  forever, until this split.

See [`docs/todo-stack.md`](todo-stack.md).

## Worth knowing

- **A generic `+$p` trust rule makes `ugm.gates.vocabulary`'s static web analysis report a false
  positive** — `cancelled`/`cause`/`delayed` now print as "nothing writes this" in `delay.ugm`'s own
  `--ask` run, because the consequent is a bare variable, not a literal pattern the scanner can see
  through. Real at load time (`<trust>` does write them), cosmetic in the diagnostic. Not fixed; would
  need the web scanner taught to trace a variable-relation consequent, which is a bigger change than
  this session's scope.
- **A comment on its own line inside a LINE-FORM rule body ends the block early** — the tokenizer
  strips comments before the parser ever sees them, so several consecutive comment lines between two
  members look exactly like the blank-line gap that ends a line-form rule. Found authoring
  `todo.ugm`'s own `<pin-todo>`. Documented in `docs/authoring.md` §5.
- **`_by_key`/`_by_arg` still never shrink on erasure** (carried over from the last handoff, unchanged
  this session).

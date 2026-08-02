# Changelog — `microfunctions/`

**What this file is for, and it was asked for by a consumer.** `../pystrider` had a pin go red mid-session
because `types.attrs_of` changed the *shape* of what it returns (a bare value became an `AttrReq`), and
from the outside there was no way to tell **"upstream grew a capability"** from **"we broke something"**
without bisecting (`feedback_microfunctions.md` §11). That is a reasonable thing to be able to tell.

**So the rule this file exists to keep:** every change to what a public function *returns* or *accepts*
gets a line here, on the day it happens, whether or not it is a "release". Behaviour changes that a caller
could not detect do not need one. When in doubt, write the line — it costs one sentence and saves a bisect.

⚠ Entries say what a consumer must **do**, not what we felt like doing.

---

## 2026-08-02 (later)

### Changed — ⚠ EDGES HAVE IDENTITY (substrate)

- **`Graph.link` / `link_at` now RETURN the edge's id**, a stable string for as long as the edge exists.
  **Migration:** none — they returned `None`, so nothing can be relying on it.
- **⚠ `Graph.eprops` is keyed by edge id, not `(src, label, index)`.** Anything reading `g.eprops`
  directly must move to `g.edge_props(eid)` / `g.edge_at(src, label, i)`. `g.edge_prop(src, label, index,
  key)` is **unchanged** and still works positionally. ⚠ We had exactly one direct reader (`workbench`)
  and it silently returned `{}` after the change — check for `g.eprops[` in your tree.
- **New:** `edge_at`, `edge_ids`, `edge_ends`, `edge_props`, `edge_between`, `is_edge`. An edge id is an
  ordinary string, so it can be a link **target** — `g.sources(eid)` answers *"what refers to this edge"*
  in O(1), which is what makes *"when did this file appear under this directory"* expressible.
- **Removed (private):** `_reindex`, `_label_props`, `_restore_props` — they existed only to shift
  properties on insertion. Properties now belong to an edge, which does not move when its neighbours do.

### Added — `clock.py`: time is a node that points at what it dates

- **`moment` / `now` / `stamp` / `dated` / `precedes` / `ordered`.** A moment carries an absolute stamp or
  none at all (relative and undefined), ordered by a `before` partial order via `path.reaches`. The
  timestamp **points at** what it dates, so one look dates many facts and nothing is modified to acquire a
  time. **No migration:** additive. ⚠ `memory.observe` now stamps every observation, and one
  `record_sighting` shares **one** moment across every slot it saw.

### Changed — ⚠ the comparison operators reach goals and conditions

- **`goal.require_attr` takes `op=` (default `"=="`)**, and `!= < <= > >=` are now legal in a goal
  constraint and in a `when`/`unless` condition, not only in a `type` block. **Migration:** none for
  existing callers.
- **⚠ Three readers changed behaviour**, and all three were previously *wrong* for anything but equality:
  `goal.holds` and `criterion._holds` evaluate the operator; `query.refutes` refutes when the comparison
  **fails** rather than when the value differs; `conflict.unsatisfiable` no longer calls two constraints
  on one slot contradictory merely because their values differ (`size > 10` with `size > 20` is fine).
  ⚠ If you relied on `unsatisfiable` flagging any differing pair, it now reports fewer — deliberately;
  the old behaviour refused achievable goals.
- **`types.compare(op, got, want, hi=None)` is public** — the one comparator all of the above share.
- **⚠ A reference on the right of a comparison is now REFUSED** (`a.size > b.size`). It was refused by
  accident before (unknown middle word → read as a link); widening made it parse as a string comparison
  that can never hold, so the refusal is explicit and names the `type` block instead.

## 2026-08-02

### Added — `norm.py`: a prohibition that can be defeated (`feedback_from_harneskills` §3)

- **`norm.declare` / `settle` / `apply` / `explain`.** A norm forbids or permits an operator, carries a
  **source**, and is `defeasible` or `inviolable` (the project's fourth force pair). ⭐ Arbitration reuses
  `discourse.authority` — **a norm's source is its speaker** — so there is no norm-specific notion of
  strength. `apply(goal)` writes ordinary `never` constraints, so nothing downstream learns a new concept
  and arbitration never enters the planner. **No migration:** entirely additive.
- ⚠ **Conflicting norms whose sources are unranked are REFUSED** (`norm.Undecidable`), naming both
  sources. Breaking the tie by declaration order would be an undeclared tie-break.
- **The answer to "is it in scope":** yes. *Anything expressable is in scope; the how is a design choice,
  and "in a consumer's Python" is not one of the available choices* — see `not_supported.md` §4.

### Added — the body-line vocabularies are data (`feedback_from_harneskills` §6)

- **`intake.FORMS` and `intake.forms_for(family)`** give the legal body-line forms per family, and every
  "vocabulary is closed" refusal now renders **from** that table. Previously they existed only as display
  strings inside raise sites, so a consumer building completion had to re-type all six grammars. **No
  migration:** purely additive. Keys are family names as they appear in refusals (`goal`, `type`,
  `advice`, `method`, `method step`, `criterion`, `condition`, `question`) — not verbs, since a force pair
  shares one body.

### Added — an ambiguous name carries its candidates (`feedback_from_harneskills` §7)

- **`intake.Ambiguous(Unreadable)`** carries `.candidates` and `.name`. **No migration:** it is a
  subclass, so every `except Unreadable` still catches it; the refusal is unchanged and only gains
  attributes, so a UI can offer the two nodes rather than making a human guess.

### Changed — `pursue` warns when authored advice cannot be consulted (`feedback_from_harneskills` §1)

- **⚠ `driver.pursue` now emits a `RuntimeWarning` when guidelines exist in the graph and `rank=` was
  not passed.** A `prefer` block parsed, minted a node, and was inert because of a keyword argument at an
  unrelated call site — indistinguishable from advice that was consulted and lost. **Migration:** none
  required, and the warning is silent when `rank=` is supplied or no guideline is declared. If you pass a
  custom ranker that deliberately ignores guidelines, you will not be warned — anything passed as `rank`
  is taken at its word.

### Changed — better refusals at the border

- **A second block header is now named as one** rather than reported as an unrecognised body line
  (`feedback_from_harneskills` §2). Same exception type; only the message differs.
- **`x l+ y` now works in a `when`/`unless` condition**, and `criterion._holds` evaluates it with
  `path.reaches` (it previously compared one direct edge). `describe_test` renders the `+`. **Migration:**
  a condition that was written with a `+` and silently read as a direct edge would have been refused
  before, so nothing existing changes meaning.
- **⚠ `goal.require_known` now REFUSES two shapes it used to accept**: a key naming an *edge*, and a key
  naming *nothing at all*. Both produced a goal that reported itself done with an empty plan, having never
  looked. **Migration:** if you relied on `x.k known` for a `k` that is an edge label or absent, it now
  raises `ValueError`; the constraint was never doing anything.

## 2026-08-01

### Changed — a prohibition now binds a goal's descendants

- **⚠ `goal.breached` now reads `never` constraints from the whole ANCESTRY, was the goal's own only.** A
  ban declared on a parent goal previously said nothing to a search planning one of its subgoals — a ban a
  child could sidestep. **Migration:** a subgoal that was reachable may now be refused, which is the point;
  nothing else changes for a goal with no parent. `at_most` and `eventually` are deliberately **not**
  inherited — see `goal.budget_of` and `goal.prohibitions` for why the three sorts differ.
- New readers: **`goal.prohibitions(g, goal)`** (own + inherited `never`) and **`goal.budget_of(g, goal)`**
  (own `at_most`, and a docstring saying why it is not inherited).

### Changed — enumeration order, effect shape, and a new frontier component

- **⚠⚠ `function.names` now returns DECLARATION order, was alphabetical.** This is the tie-break
  `driver.proposals` enumerates in, so it decides which world is imagined first wherever two proposals
  score alike. It was measurably load-bearing: the same function renamed `buy_ticket` → `zz_buy_ticket`
  took a search from 3 imagined states to 17. **Migration:** nothing in the signature changes, but any
  recorded *cost* figure taken before today may move — guided figures did not move in our measurements,
  blind/unguided ones moved by up to 2.4x. If you pin a step count, re-measure. ⭐ An author can now order
  a library and have it mean something; `driver.py` has documented this order as declaration order all
  along, and it was not.
- **⚠ `driver.establishes` — an `attr` effect's fourth element is now the VALUE WRITTEN, was always
  `None`.** The tuple is `(kind, label, subject_role, fourth)` and the fourth slot is tagged by the first:
  for `link` it remains the object role, for `attr` it is the value, or the sentinel `driver.UNREADABLE`
  when the body computes it. **Migration:** a consumer pattern-matching `("attr", key, role, None)` must
  now match the value (or `driver.UNREADABLE`). `None` is a legitimate attribute value, which is why the
  sentinel exists rather than reusing `None`.
- **`driver.proposals` is unchanged**; new `driver.enumerate_frame(g, frame, allow=)` returns
  `(proposals, blocked_function_names)`, and `proposals` is a wrapper over it. New:
  `driver.wants_that_unblock`, `driver.unlocks`, `driver.stands_for`, `driver.UNREADABLE`.
- **The search frontier key gained a component**, `(expected, -band, -unlocks, depth)`, was 4-tuple
  without `-unlocks`. Internal to `driver`/`search`; a caller passing `rank=` is unaffected, since a
  custom ranker still supplies the band.

### Fixed — a `TypeViolation` no longer escapes `execution.step`

- **`execution.step`** now catches `types.TypeViolation` from the call it makes and records an ordinary
  **`deviation`** instead of letting it propagate. A plan whose precondition went false while it was
  suspended used to raise straight through `execution.step`, `driver.pursuit_step` and `loop.tick` —
  stranding that pursuit mid-`acting` **and killing every other task on the agenda with it**. The
  deviation carries `stale_precondition=True`, `param`, `expected` and `violations`, so the existing
  recovery ladder applies unchanged. **Migration:** a caller that wrapped `execute` / `pursuit_step` /
  `loop.tick` in `except TypeViolation` to survive this will now see the failure as a normal deviation
  report instead; the exception no longer arrives. ⚠ `result` is `None` on this deviation, so
  `matching_alternative` declines and recovery goes to replanning — correct, because the call never ran.
- **`function.invoke`** now attaches `function`, `param`, `want` and `violations` to the `TypeViolation`
  it raises. Purely additive; the message is unchanged.

### Changed — return shapes

- **`types.schema_of`** now returns `{label: Req}` instead of `{label: (target_kind, count)}`.
  `Req(kind, type, lo, hi)` is a `NamedTuple`; a count is now a **range** and a target may be constrained
  by declared type as well as by graph kind. **Migration:** `kind, n = schema[label]` becomes
  `req = schema[label]` then `req.kind`, `req.lo`, `req.hi`. Writing `{"wheel": ("wheel", 4)}` into
  `declare_type` is still accepted and still means exactly four of that kind.
- **`types.attrs_of`** now returns `{key: AttrReq}` instead of `{key: value}`. `AttrReq(op, value, hi)`
  carries a comparison (`== != < <= > >= between`). **Migration:** `want = attrs[key]` becomes
  `attrs[key].value` where the old code assumed equality. Iterating for *keys* is unaffected.
  ⚠ This is the change that broke `../pystrider`'s pin, and the reason this file exists.
- **`types.requirements`** now returns a 3-tuple `(schema, attrs, rels)`, was 2. `types.fails` takes that
  3-tuple. Both are pass-through for most callers.

### Added

- **`path.py`** — the reference language, extracted from three undeclared copies. `car.wheel[1].pressure`,
  unbounded depth, `^label` for a backward hop (resolving only when exactly one node points that way).
  `driver.role_node` now goes through it; behaviour there is unchanged.
- **`types.Req` / `AttrReq` / `Rel`**, and `types.rels_of`, `types.describe`, and the incremental authoring
  functions `require_edge` / `require_value` / `require_relation`.
- **`Rel`** relates two places inside one subgraph — `wheel[0].pressure == wheel[1].pressure`. This is the
  join `feedback_microfunctions.md` §5 said a schema structurally could not express. It can now.
- **Recursive schemas.** `Req(type=…)` checks the target against its own schema, to any depth,
  coinductively (so `person.friend: person` terminates on two mutual friends).
- **`type` is the eighth CNL verb.** `intake.read` accepts a `type …:` block; `types.describe` renders one
  back to the text it was authored in.

### Fixed

- **`isa`: a write through an unset register is refused instead of minting an edge to `None`**
  (`feedback_microfunctions.md` §10). `LINK`, `LINK_AT`, `UNLINK`, `DROP`, `SETREF` and `SET`'s *subject*
  now raise `RuntimeError` naming the opcode and the operand; `run` rolls back, so nothing is left behind.
  ⚠ **Consumer impact:** a program that previously "succeeded" while writing a null edge now fails loudly.
  A `SET`'s *value* may still be `None` — that is an ordinary attribute value, distinct from `UNKNOWN`.
- **`function.invoke` enforces declared parameter types** (`feedback_microfunctions.md` §9), which were
  previously checked only by `driver.proposals`. ⚠ **Consumer impact:** a call that violates a signature
  now raises `TypeViolation` where it used to run. Pass `check_types=False` to opt out. An **undeclared**
  parameter type also refuses, matching `driver.proposals`, which already treats one as satisfiable by
  nothing. A parameter with no declared type at all is unconstrained and unaffected.
  Consumers carrying a `CHECK` as the first instruction purely to enforce a signature can drop it.

### Added — the search's own state is graph data

- **`search.py`** — `pursue`'s frontier, visited set, step count and refusals were Python locals; they are
  now `search` / `candidate` / `candidate_arg` / `trace_step` / `signature` / `refusal` nodes. ⚠ **No
  semantics changed** in this slice, deliberately, so the existing checks are a real oracle for it.
- **`pursue`'s report carries `search`** — the node — so a caller can ask what the search already
  considered (`search.considered`), what it refused and why (`search.refusals`, `blocked_by`), and what is
  still on the frontier. Purely additive; every existing report key is unchanged.
  ⚠ `refused` is now built from the graph rather than a list, but the shape `((function, reasons), …)` is
  the same one it always had.
- **`driver.step(g, search, …)`** — one iteration of the search. Returns `None` while it should continue,
  and the finished report when it should not. `pursue` is now a loop over it and is **unchanged in
  behaviour**; `step` is a seam, not a replacement. A caller can drive a search by hand, pause between two
  imagined states, inspect it, and resume — verified against `pursue` on the same goal for both plan and
  cost.
- **`search.context(g, search)`** — the graph-resident half of a step's context. The hooks (`rank`,
  `allow`, `trace`, `decide`) stay Python callables passed per call.
- **Two ISA opcodes: `PLAN R(dst), F(goal), F(subject), F(thread)` and `STEP R(more), R(search)`.**
  A `.mf`-authored microfunction can now drive the planner and read its answer. `PLAN` returns the search
  node; `STEP` performs one iteration and answers `True` while it should continue.
- **`driver.open_planning(…)`** — opens and seeds a search, returning the node. `pursue` and `PLAN` share
  it, so there is one setup rather than two that could drift.
- **The search's outcome is graph data**: `done`, `found`, `how`, `length` attributes and a `reached` edge
  on the search node. The report dict is a convenience for Python callers, not the only place the answer
  exists.

- **`plan` is a CNL verb** — a fourth force on the goal body (`GOAL_VERBS` is now
  `("goal", "ask", "why", "plan")`). `intake.respond` pursues it and returns the plan.
  ⚠ It cannot touch the world: the search is entirely on a workbench. `read_goal` still refuses a `plan`
  block, as it refuses `ask` and `why`.

### Fixed — `asm`

- **`asm` accepted `WRITES_REGISTER` as an opcode.** `_OPCODES` filtered `isa.__all__` on `isupper()`
  alone, so a non-opcode export loaded fine and failed opaquely inside the interpreter. Now filtered on
  `callable`. ⚠ **Consumer impact:** a program containing such a token now fails at load with a line
  number, which is where it always should have failed.

### Added — memory

- **`memory.py`** — sightings, and attribution of change. `observe`, `sightings`, `believed`,
  `transitions`, `attribute`, `volatility`, `describe`.
- **`dispatch.service` gains `remember=`** (a `keep(slot) -> bool` seam, **inert by default**) and now
  records a sighting of the target after a tool runs, when it can derive the thread from `record_on`.
  ⚠ **Consumer impact:** none unless you pass `record_on`; nothing else changes, and `commit()` semantics
  are untouched. New node kind `observation`, appended to the thread like an application.

### Added — the INTERPRETER's own state is graph data (⚠ two breaking signatures)

- **`activation.py`** — `pc`, the call stack, the registers and what a call minted, as `activation` and
  `register` nodes. `isa.Machine._loop` was an ordinary Python `while`; it is now `Machine.tick`, one
  primitive operation, and `Machine.run` is a loop over it and contains no interpreter of its own.
- **⚠ BREAKING: `Focus()` is now `Focus(g)`.** A focus is a `focus` node and each head is a `head` node
  with an `at` edge, so the class needs the graph it lives in. **Migration:** pass the graph —
  `Focus().open("h")` becomes `Focus(g).open("h")`. Every method signature is otherwise unchanged, the
  navigation methods still take `g`, and an emptied head is still distinct from a closed one.
- **⚠ BREAKING (behaviour): `Machine.run` retires its activation by default.** The `(g, focus, regs)`
  return is unchanged and `regs` is read out before retirement, so ordinary callers see nothing new. Pass
  `retire=False` to keep the finished activation for inspection. `function.invoke` already does.
- **`Machine.start(g, focus, *, of=, caller=, label=, **regs) -> activation node`** and
  **`Machine.tick(g, act) -> bool`** — the yield point. `True` while there is more to do.
- **`Machine.run` gains `of=` / `caller=` / `label=`**, passed through to the activation. `of` is the
  stored `function` node, which is what lets `activation.doing` name the instruction a pause landed on.
- **`function.invoke` gains `caller=`** (an activation node) and now runs with `retire=False`, so the
  returned focus can be turned into the call's activation with `activation.for_focus`. The `(focus, regs)`
  return shape is unchanged.
- **`activation.minted(g, act)`** — exactly what a call created, its callees included. ⚠ This replaces the
  `before = set(g.nodes)` … `set(g.nodes) - before` diff inside `workbench.step` and `execution._replay`.
  A consumer reading `execute(...)["deviation"]["minted"]` gets the same shape and a **more precise** list:
  the diff also counted anything else minted while the call ran.
- **`workbench.step`'s transformation gains a `ran` edge** to the activation that imagined it, and
  `workbench.discard` scraps it along with everything else.
- **New node kinds:** `activation`, `register`, `focus`, `head`. All metadata — they point at the world and
  nothing in the world points back — so `workbench.reachable` never copies one.

### Added — the OUTER LOOP, and the last two Python control loops

- **`loop.py`** — one ordered agenda, `tick` advances the head task by **one primitive step** and rotates
  it to the back, `run` is a driver over `tick`. It advances any of `activation` / `search` / `replay` /
  `pursuit`. `verb_of(g, task)` answers `imagine` / `look` / `act` / `run` **before** the step is taken;
  `IRREVERSIBLE` is the set to decline on.
  ⚠ `advance` **refuses** an `activation` with no `of` — an anonymous program cannot be reconstructed
  from the graph and so cannot be driven by anything but the Python caller holding it.
- **`execution.step(g, replay)`** and **`execution.open_replay` / `open_execution` / `report_of` /
  `deviation_of` / `bindings_of` / `bind` / `bound_to` / `is_bound` / `finished` / `discard_replay`.**
  `execute` is now a loop over `step` and its **report shape is unchanged** (plus a new `replay` key).
  ⚠ `execution._replay` is gone; it was private.
- **`execution.resume_replay(g, result, …)`** returns the contingency's replay node, ready to step;
  `resume` is that plus the loop, and its report is unchanged.
- **`driver.open_pursuit` / `pursuit_step` / `pursuit_report` / `describe_pursuit`**, and the phase
  constants `PLANNING` / `ACTING` / `RECOVERING` / `CHECKING` / `SETTLED`. `carry_out` is a driver over
  `pursuit_step` and its report is unchanged (plus a new `pursuit` key).
- **`dispatch.register(name, handler, *, observes=False)`** and **`dispatch.observes(name)`**. ⚠ The
  default says a tool *changes* the world, which is the safe assumption; mark read-only tools explicitly if
  you want them classified as `look`.
- **A contradictory goal is recorded on the SEARCH** (`contradictory=`) rather than short-circuited inside
  `pursue`, so every driver reports it identically. `pursue`'s report for that case is unchanged apart from
  now carrying `search`.
- **New node kinds:** `loop`, `replay`, `bound`, `deviation`, `pursuit`, `attempt`. All metadata.

### Added — a rule can stop a computation it is watching

- **`stop` on a `search` node is honoured by `driver.step`.** Write `stop` (truthy, or one of the stop
  verbs) and optionally `stop_why`; the search reports exactly as a `decide` verdict does — one
  `_stopped` report builder serves both, so the two routes cannot drift. This is the `decide` hook
  expressed as **data**: `decide` stays, and is still the right thing for a per-proposal decision.
- **`stop` on ANY task is honoured by `loop.finished`**, so "stop this" means the same for an
  `activation`, a `search`, a `replay` or a `pursuit`. ⚠ Stopping a `replay` means *do not take the
  next irreversible action* and leaves a plan half carried-out — honest rather than new, since a
  divergence already does, and nothing is ever undone.

### Added — forgetting

- **`forget.py`** — `roots` / `keepers` / `doomed` / `kept_because`, and `open_forgetting` / `step` /
  `finished` / `describe`. A mark-and-sweep whose root set is *what cannot be re-derived*: the world, the
  library, intent, the thread, **the result of a tool call**, **a surprise**, and anything on a live
  agenda. ⚠ Everything else is dropped — searches, candidates, frames, mappings, replays, activations,
  registers. Measured 892 to 238 nodes on a three-goal session, with every answer unchanged.
- **`forgetting` is a task kind** on `loop`, one record per tick, with verb `loop.FORGET`. Nothing runs it
  for you; schedule it when you want it.
- ⚠ **Consumer impact:** none unless you schedule a pass. If you do, anything you hold a Python
  reference to but that no root reaches **will be dropped** — pin it with
  `open_forgetting(also=(node,))`, or schedule it on a loop.

- **`forget.compact(g)`** — drops `seen_in` / `planned_witness` from goals that are `closed`, i.e.
  imagined evidence superseded by real evidence. Runs eagerly inside `open_forgetting`; pass
  `compacting=False` to skip it. ⚠ A goal that is planned and **not** closed keeps its imagined frame,
  which is the correctness condition, not an optimisation.

### Added — transitive reach

- **`path.reaches(g, start, label, dst, *, back=False)`** — is `dst` reachable by **one or more** `label`
  hops? Cycle-safe, breadth-first, never reflexive.
- **`path.via(g, start, label)`** — everything so reachable, nearest first. ⚠ Not wired into any path: a
  reference must denote one node, and this denotes a set.
- **`path.parse_link(text)`** — `"contains+"` → `("contains", True)`. For a **link position** only;
  `path.parse` still refuses `+` in a reference, and now names the predicate form in the message.
- **`goal.require_link(..., transitive=True)`** — reach instead of adjacency. Stored as the same `link`
  sort with a `transitive` attribute, so every other reader of a constraint is unaffected;
  `describe_constraint` renders it back as `wh contains+ parcel`.
- **The CNL link form accepts `a b+ c`** in a goal / ask / why / plan body.

### Refused, deliberately — so nobody reports it as a bug

- **A reference reaches any depth in a `type` block, one hop in a `goal` or `method` one.** Deeper is
  refused loudly at intake rather than mis-parsed. It used to be silently mis-parsed:
  `a.wheel[1].pressure = 3` split on the first dot and produced a constraint about an attribute *named*
  `wheel[1].pressure`. What blocks the honest version is downstream — `conflict.unsatisfiable` keys a slot
  as `(subject, key)` and would read two wheels' pressures as one contended slot, and `goal.holds` /
  `query.refutes` read the attribute off the base node. See `HANDOFF.md` §5v.

### Added — the wh-questions: `what` / `where` / `when`

- **`locate.py`** — `what` (which declared types a node satisfies now, = `types.recognize`), `where` (what
  holds it, at any depth, nearest first), `when` (how its interval stands against every other dated thing).
  Plus `interval`, `relate` (Allen's thirteen relations), `locate` and `describe`.
  ⚠ **A reader records nothing.** Every answer is a traversal away, so keeping one could only let it drift.
- **`locate.where(g, node, by="^contains")`** — `by` is one hop written **as walked from the thing**, with
  `path.py`'s `^` for the backward direction. A world writing the relation the other way is asked with
  `by part_of`; nothing here is wired to a containment vocabulary. This is the caller `path.via` was added
  for and did not have.
- **`locate.relate(a, b)`** returns `None` when the endpoints are not comparable — incomparable is a third
  answer, not `before`.
- **Three more CNL verbs.** `intake.VERBS` now includes `what`, `where`, `when` (`intake.READER_VERBS`).
  ⚠ **Their body is different from every other block's**: one bare name per line, or `by <label>`. They
  produce a `question` node (new kind) with ordered `about` edges, and `intake.respond` returns the
  **answer text**; nothing is written to the world. `intake.describe` renders a question back to what was
  *asked*, never to what was answered. `read_goal` refuses them, as it refuses `ask` / `why` / `plan`.
  ⚠ **Consumer impact:** if you match on `intake.VERBS` or on the set of block headers, there are three
  more. Nothing existing changed shape.

### Added — witnesses for a universal constraint (`plural_step.md` slice A)

- **`types.offenders(g, node, type_name)`** → `{label: (node, …)}` — which targets make a node fail a
  type, empty when it passes. ⚠ Only the **too-many** direction has witnesses: `has no file each a
  ungone_file` blames the un-gone files, while `has 4 wheel` with three wheels has nothing to point at,
  because the missing wheel does not exist. The too-few direction is served, from the other side, by
  `relevance`'s existing existential branch (an operator that MINTS one).
- **`types.offending_type(g, type_name, label)`** → the type a target must stop satisfying, or `None`.
- **`goal.witnesses(g, c, *, view=, under=)`** → the nodes that must change for one constraint to become
  true, in the same world `holds` looked at. `()` when the constraint holds. For attr/link/known sorts it
  is the subject, so one uniform question serves every sort and no consumer branches to ask it.
- **`workbench.original_of(g, node)`** → the real node an image stands for, identity for a real node.
  `driver.view_in`'s inverse, which existed only as an inline idiom.
- ⚠ **Behaviour change: `driver.relevance` can now score band 4 for a `type` constraint with a subject**,
  when the call writes something that could stop a witness from offending. Previously such a constraint
  could reach at most band 1, so *"all the files are deleted"* was effectively unguided. **Consumer
  impact:** proposal ordering changes for goals containing a subject-bearing type constraint; nothing else
  moves — the engine's measured search costs are unchanged (guided vs blind still 2 vs 67, role paths
  still 3/10/10). `relevance` keeps its four-argument signature: the frame is **recovered from the
  bindings** rather than passed, so no `rank=` hook and no `guideline.compose` caller changes.
- ⚠ Witnesses are **derived, never stored** — §5f refused to materialise expectations for the same reason
  (the driver imagines hundreds of frames) and §5i is the other half (a stored list is a claim about the
  past; this is a question about now).

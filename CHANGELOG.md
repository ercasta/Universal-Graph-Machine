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

## 2026-08-01

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

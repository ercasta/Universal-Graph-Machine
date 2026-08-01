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

### Refused, deliberately — so nobody reports it as a bug

- **A reference reaches any depth in a `type` block, one hop in a `goal` or `method` one.** Deeper is
  refused loudly at intake rather than mis-parsed. It used to be silently mis-parsed:
  `a.wheel[1].pressure = 3` split on the first dot and produced a constraint about an attribute *named*
  `wheel[1].pressure`. What blocks the honest version is downstream — `conflict.unsatisfiable` keys a slot
  as `(subject, key)` and would read two wheels' pressures as one contended slot, and `goal.holds` /
  `query.refutes` read the attribute off the base node. See `HANDOFF.md` §5v.

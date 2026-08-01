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

### Refused, deliberately — so nobody reports it as a bug

- **A reference reaches any depth in a `type` block, one hop in a `goal` or `method` one.** Deeper is
  refused loudly at intake rather than mis-parsed. It used to be silently mis-parsed:
  `a.wheel[1].pressure = 3` split on the first dot and produced a constraint about an attribute *named*
  `wheel[1].pressure`. What blocks the honest version is downstream — `conflict.unsatisfiable` keys a slot
  as `(subject, key)` and would read two wheels' pressures as one contended slot, and `goal.holds` /
  `query.refutes` read the attribute off the base node. See `HANDOFF.md` §5v.

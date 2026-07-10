# Walkers, locality, and shortcuts — the connection model

> **Status: DESIGN (2026-06-30), with the lower layers already built.** This is the
> resolution of "how does locality-bounded matching work on a substrate whose join key
> is the node *name*, not graph adjacency." It builds on `vision.md` §11 (locality),
> §14 (the metareasoning layer), §6 (control as token-passing), §3 (coreference), and
> §5 (the two layers). It refines §11. Companion: `memory/finding_matcher_is_matching_bound.md`.

The whole model is one chain of consequences:

> **Seed only from ground positions (prefer the rarest); free variables are destinations,
> not origins → a rule with no ground anchor must be demand-driven → long-range / iterative
> work is done by *walkers* (control tokens carrying an origin + a frontier + a fuel budget)
> → what a walker discovers is materialized as an ordinary *shortcut* chain (a derived fact,
> or a `same_as` link), provenance-bearing, so future reasoning is local and cheap → "radius"
> is not a matching neighbourhood, it is the walker's fuel → "the rules near a locus" (a
> change-delta or a walker position) are found by the lexical index, recomputed as the locus
> moves.** Every dial in here is content-blind (§14).

---

## 0. What is already built (the measured baseline)

Profiling (`finding_matcher_is_matching_bound`) overturned the assumption that the engine
was firing/output-bound: it is **matching-bound** (`_triples` → `Graph.succ/pred`). Landed,
86 tests green, suite ~1.2s:

- **Tier 0 (the decisive win):** `Graph.succ`/`pred` = live read-only neighbour views (no
  per-call set copy); the hot matcher uses them. `nac_blocks` fast-paths a fully-bound NAC
  to an O(degree) existence check instead of rebuilding `set(graph.nodes())`. chain n=40
  10,730ms → 1,709ms (~6.3×); n=70 212s → 17.6s (~12×).
- **Tier 2:** `delta_matches` (semi-naive) restricts a woken rule to bindings using ≥1
  relation node from the change frontier. Modest on closures, a no-op once locality bounds
  the scope; correct (identical-results guard vs the naive engine).
- **`Rewriter`** — the stateful engine, holding per-rule anchors as supporting machinery
  *outside* the graph (the home for everything below). Anchor-delta activation lives here
  but is ~inert atop the lexical index (kept as scaffold).
- **Fixed:** `Graph.copy()` never rebuilt `_by_name`, so matching on a copy found nothing.
- **`vision.md` §14** — the metareasoning layer (content-blind effort policy) + §12.7 guardrail.

The findings that *motivate* the rest: rule-level activation is inert because the index
already makes a non-matching rule's attempt ~O(1); the real cost is rules that re-scan a
large scope; and locality-by-hops is mismatched to a name-keyed join (the `paul is_a mortal`
failure under per-line seeding).

**Step 1 (seed-from-ground) is now BUILT too (2026-06-30, 88 tests green).** `rewriter._triples`
no longer scans the whole scope for an all-free pattern; it seeds from the most selective GROUND
position (fewest in-scope candidates), or yields nothing if none is ground. Measured: chain n=40
1,709ms → **359ms**, n=70 ~16,070ms → **2,365ms** (~5–7× on top of Tier 0; ~30× cumulative from
session start). The win is automatic anchor selectivity *and* — the big one — transitivity's join
step now seeds its second pattern from the already-bound `?b` (one node) instead of scanning every
`is_a`. Two tests lock it (`test_seed_from_ground_never_scans_for_a_free_pattern`,
`test_seed_from_ground_prefers_the_rarest_anchor`). See §8 for what step 1 did *not* do (the
cross-pattern join reorder) and step 2.

---

## 1. The principle: seed from ground, never from the unknowns

A match must be **seeded from a ground position** — a literal (`is_a`, `person`) or an
already-bound variable — **never from a free variable.** Free variables are what the match
*solves for*; seeding from one means "start from anywhere," i.e. the whole-graph scan.

This is the database / magic-sets / sideways-information-passing rule (drive from the bound
columns, pass bindings on), and it is *almost* how `rewriter._triples` already works — the
single violation is its `else:` branch that scans all of `scope` when `s`, `p`, `o` are all
free. Under this principle:

- A pattern with no ground position is reached only by a **join** from another pattern's
  binding (which makes its variables bound = ground at runtime).
- A rule where *every* pattern is all-free has **no seed at all** → it cannot run eagerly;
  it must be **demand-driven** (a query/goal/walker supplies the starting binding). The
  all-free scan branch should therefore be removed, not relied on.

**`df` (name frequency, §14) is not a separate rule — it is just which ground anchor to pick
when there are several: the rarest (most selective).** So: *seed from ground, prefer the
rarest; variables are destinations, not origins.* This subsumes both the df-selectivity idea
and anchor-delta activation (a rule whose rarest ground anchor has `df = 0`, or is absent
from the delta, does no work — for free).

**The honest residue:** transitivity's only ground anchor is `is_a` (borne by everything).
The principle correctly refuses to seed from `?a/?c`, but `is_a` is still huge — so eager
transitivity stays expensive. That is the demand-walker case (§4), not an eager rule.

---

## 2. One matching strategy, both layers — control self-bounds

There is **no separate "control scope" mechanism.** Control rules match a control token and
bind facts parametrically (`?x`), and the control token is **low-df** (a `<current>`/`<goal>`
is typically one live instance — measured: coffee after `plan()` has `<now>=1, <goal>=1,
<need>=1, <yes>=1`). So "seed from the rarest ground anchor" *starts control matching at its
token* and expands only along the parametric fact-bindings around it. Control self-bounds for
exactly the reason reasoning is cheap.

Consequence: the §5 reasoning/control split stops governing **scope**. It governs only
**delete-permission** (control may delete control/ephemeral edges; reasoning never deletes)
and **provenance** (on for reasoning, off for the churning control loop). Matching is one
strategy for both.

> Note `?x` (a free variable — binds *any* node) is what a walker uses to traverse facts;
> `x?` (a bound-literal — binds a node *named* x) is for pinning a specific named node. The
> traversal step needs the free variable.

---

## 3. Two connection channels

Reasoning connects nodes through two channels. Conflating them was the original confusion.

- **Path connection** — nodes joined through **shared graph edges** (transitivity's two
  `is_a` facts share the middle node `?b`; a context-scoped rule threads `?shop`). These are
  graph-local: the join follows real edges and terminates on the data.
- **Name connection** — nodes related by **sharing a name**, which the lexical index makes an
  *implicit* edge. A single-pattern law `?u is_a person` finds `paul`'s (graph-disconnected)
  `person` mention directly through the index. This is why `paul is_a mortal` was a *name*
  problem, not a radius problem — no path connects them; the index does.

Seeding from a ground literal opens the **name** channel globally (find every `person`);
following shared-variable edges opens the **path** channel locally. df decides which name
channel is cheap to open.

---

## 4. Walkers — variable-length traversal as control

The fixed-arity pattern language cannot say "A connected to Z via *some* path" (the old
decision #5 limit). The §6 way around it is a **walker**: a control token that carries

- `origin → A` (where it started — one of the extremes),
- `frontier → current` (where it is now — the other extreme),
- a **fuel** budget (how far it may still go).

Each step is an ordinary fixed-arity rule, self-bounding because it is seeded on the (rare)
walker token and binds the next fact parametrically:

```
walker frontier ?x , ?x rel ?y  ⇒  move walker frontier to ?y   (consume 1 fuel)
```

When `frontier` reaches the target `T`, a rule fires the connection `A rel T` — and **both
extremes are in hand** because the walker carried the origin the whole way. A plain
`<current>` that only knows "here" cannot do this; carrying `origin` is the point.

Walkers are **demand-spawned** (a query/goal needs A↔Z), never eagerly for all pairs — else
walker-closure is the same blow-up as eager transitivity. They are how the all-ground-anchor
expensive rules (§1 residue) actually run.

**Termination** needs a **visited marker** (so a cyclic `rel` doesn't loop forever) plus the
fuel budget as a backstop. (`is_a` is kept acyclic by the constraint schema; general
relations are not.) This is the well-foundedness concern the coreference design deferred,
returning here in control form.

---

## 5. Shortcuts — materialized discoveries

When a walker connects A to T across many hops, it **materializes a shortcut**: an ordinary
edge-node chain `A rel T`, identical in kind to any other relation — **only shorter**,
because it does not re-traverse the hops. **No new edge type** (vision §1 stays intact); a
shortcut is just a derived fact.

The two channels both materialize:

| channel | discovery (expensive) | materialized shortcut (cheap thereafter) |
|---|---|---|
| **path** (transitivity) | a fuelled walker | the derived fact (`a0 is_a a_n`) |
| **name** (`paul`/law) | the lexical index | a `same_as` link (coreference, §3) |

So **coreference is shortcut-materialization for the name channel**, exactly paralleling
derived-fact materialization for the path channel. Both turn an expensive discovery into a
cheap cached edge, which **lowers future fuel** — the graph *compiles* its own
frequently-traversed paths.

Two requirements:

1. **Provenance is mandatory, not optional.** A shortcut bypasses its hops, so "why does
   A rel T?" has no visible derivation unless the walker records the compressed path:
   `J --proves--> (A rel T)`, `J --uses--> each path edge` (the existing `provenance.py`
   machinery). This also makes the shortcut **retractable**: if a path fact is later
   withdrawn, the cascade invalidates the shortcut.
2. **Shortcuts inherit their layer's (non)monotonicity.** Path/derived-fact shortcuts are
   monotone → permanent, always safe to trust. Coreference `same_as` shortcuts are
   **defeasible** → if disambiguation later flips, the quarantine/cascade (`retraction.py`)
   must invalidate them. So the name channel *needs* the TMS; the path channel does not.

---

## 6. "radius" is walker fuel — the §11 refinement

Given §2–§5, **`within`/radius as a *matching neighbourhood* can retire.** Eager rules seed
from a selective ground anchor and join along real edges (no neighbourhood bound needed);
control self-bounds on its token; the only thing radius ever really bounded — long
unselective paths — becomes a **walker's fuel budget.** "Think harder" = more fuel = explore
further before giving up; and a materialized shortcut means the walker reaches the target in
fewer steps next time, so *less* fuel is needed as the graph compiles.

This refines `vision.md` §11. The precise edit:

- §11 currently presents the **hop-radius** as the universal effort knob and the matching
  strategy. Recast: the matching strategy is **seed-from-ground (§1)**; the universal effort
  knob is **walker fuel** for deliberate long-range/iterative exploration; df-selectivity is
  the eager-matching effort signal. Hop-radius-as-matching-neighbourhood is demoted (and, if
  validation confirms nothing relies on the all-free scan, removed).
- Keep §11's "semi-naive evaluation" and "lexical indexing" lessons verbatim — they are the
  mechanism §1 rides on.

> This is a meaningful edit to canonical text describing a *built* mechanism (`within` is in
> use), so it is staged here rather than overwriting §11 until the walker layer is built and
> validated. §11 carries a forward-pointer to this doc.

---

## 7. Walker locality — the RETE concept, done right (not frozen)

You do **not** need a separate "RETE for walkers." A walker is a **persistent, named, moving
delta-of-one** — a ground locus that carries bindings and fuel. The single rule "activate the
rules **anchored at the active ground loci**" already covers both kinds of locus:

- transient **change-deltas** (eager reasoning), and
- persistent **walker positions** (control / exploration).

So "the rules near a walker" = "rules whose ground anchor sits at the walker's current
position," **found via the lexical index and recomputed as the walker steps.** Different
walkers have different near-rules *automatically* (they are at different positions) — which
gives **concurrent control flows** (one walker doing transitivity, another planning), each
firing only its relevant rules, for free (vision §6's "concurrent loops each hold their own
token").

**The rigidity trap is *freezing* a fixed rule-set onto a walker.** That would (a) break
reasoning's openness (§6 "any enabled rule fires" — you'd pre-decide which inferences may
occur) and (b) be unnecessary (the position already determines the near-set). So: derive the
near-set from position (locality — not rigid); **freezing is an opt-in specialization** for
where the control flow genuinely *is* a fixed state machine (walker = state, near-rules =
transitions), never the engine default.

**Do not walker-ify everything.** Cheap eager inference (seed from a rare concept, fire once)
is one-shot match-and-fire — no walker. Walkers are for *iterative / multi-step / long-range*
work. A walker's newly-created fact is itself a fresh locus, so consequences propagate through
the ordinary delta mechanism — walkers and eager firing compose, they are not alternatives.

Policy vs mechanism (the §14 line): *which* walkers to spawn, their fuel, whether to ever
cache a near-set = metareasoning (content-blind). Computing "rules anchored here" via the
index = engine. Keep that line so a "smart" walker scheduler does not smuggle the rejected
planner (§6/§10) back in.

---

## 8. Open problems and build order

**Open / to-validate**

1. ~~Remove the all-free seed scan~~ — **DONE** (no shipped rule had a variable predicate, so
   none relied on it; `match` of an all-free pattern now yields nothing, by test).
2. ~~**Shortcut provenance** wiring~~ — **DONE** (`walker.py`). The walker keeps the reached
   set *additive*, so each `reached ?y` is justified by `J --uses--> [reached ?x],[path ?x->?y]`;
   the shortcut hangs off the permanent `reached(T)`, so its provenance chains hop-by-hop to
   every path edge, and `cascade_retract` of a *middle* path edge withdraws the shortcut (test).
3. ~~**Walker termination**~~ — **DONE.** The `reached`-NAC is the cyclic-`rel` guard (a node
   reached once is never re-added → finite); fuel is the §14 backstop budget on top
   (test_walker_terminates_on_cyclic_relation, test_walker_respects_fuel_budget).
4. **Validate retiring `within`** — confirm the eager path joins terminate cheaply on real
   data without a neighbourhood cap, and that control self-bounding holds across the planning
   loop's control structure (where tokens attach to operator/fact nodes).
5. **The all-ground-anchor expensive rule** (transitivity) is demand-walker-only; never run
   it eagerly. (Eager transitivity is now ~6× cheaper via step 1, but still O(closure) firings.)
   On-demand transitivity now has a *walker* realization too (`walk_on_demand`), selective by
   construction — only the demanded `A is_a T` is materialized.

**Suggested build order**

1. ~~Seed-from-ground in `_triples`~~ — **DONE (2026-06-30).** Seeds from the most selective
   ground position; no all-free scan. ~5–7× on closures (~30× cumulative). Subsumes anchor-delta.
1b. **(Optional refinement, not done)** Cross-*pattern* join reorder — match the rule's
   lowest-df *pattern* first, not just the lowest-df position *within* a pattern. Step 1 reorders
   within a pattern and benefits automatically from bound-variable seeding on joins, so this is a
   smaller marginal win; do it only if a profile shows a rule wasting work on a high-df first
   pattern before a df-0 later pattern kills it.
2. ~~A minimal **walker gadget**~~ — **DONE (2026-06-30, `walker.py`, 95 tests).** Token with
   origin + reached + target + fuel; step rule (advance reached one hop, burn a fuel unit,
   `reached`-NAC for cycles) + shortcut-on-arrival rule (materialize `A rel T`), provenance on,
   demand-spawned via `walk_on_demand` (reuses `demand.py`: `<demand>` → DEMAND_WALK rule →
   `<walk-request>` → `service_walk_requests` dispatcher → `spawn_walker`; FUEL is §14 driver
   policy). First target: on-demand transitivity along `is_a`. **Key realization choice:** the
   reached set is *additive* (a retained BFS wavefront), not a single moving frontier — it
   unifies §4's frontier + visited marker, finds any path, and gives clean compositional
   provenance (each hop's `J --uses--> [reached ?x],[path]`). Semi-naive matching (default)
   restricts each step to *newly* reached nodes, so retaining the set costs no re-scan — it
   behaves like a moving frontier for free. Walkers bind `<walker>?` (bound-literal) so two
   concurrent walkers never cross-wire (test_two_walkers_do_not_cross_wire — a down payment on
   §7). *(Validated §4, §5, §6.)*
3. ~~Recompute near-rules from walker position via the index; demonstrate two *fully*
   concurrent walkers (different relations / near-rule sets).~~ **DONE (2026-06-30, 113 tests).**
   `near_rules(graph, rules, locus)` (rewriter.py) returns the rules the lexical index would
   seed from a node — its LHS has a ground anchor matching the node's NAME. Walkers are now
   TYPED by their token (`walk_rules(rel, token=…)`, `spawn_walker(…, token=…)`): two walkers
   with different tokens get DISJOINT near-rule sets *automatically* (no frozen per-walker
   rule-set), so an is_a walker and a part_of walker run in ONE `run()` from the SAME origin
   (which has both edge kinds) with zero cross-wire — each reaches only its relation's subgraph
   and fires only its own rules (by the journal). *(Validated §7.)* Content-blind (names +
   anchors only, §14). The engine's existing predicate-name activation is the coarse
   approximation; `near_rules` is the precise per-locus version (an inspection/validation
   helper here, a candidate activation driver later).
4. ~~Once 2–3 hold, apply the §11 edit to `vision.md` and retire `within`-as-matching-scope.~~
   **DONE (2026-06-30, 114 tests).** `rewriter.run` scope is now the whole graph (the single
   `graph.within(...)` call is gone); validated that the full suite stays green at the same
   speed AND that a 40/70-hop transitive closure completes *correctly* under `radius=1/3` (which
   the old hop-bound would have truncated) — proof that matching no longer depends on radius for
   correctness or speed (test_matching_is_unbounded_radius_is_ignored). `radius` is kept as a
   vestigial, ignored parameter (no call-site churn); `Graph.within` stays as a general utility,
   no longer the matcher's mechanism. `vision.md` §11 recast: seed-from-ground is the matching
   strategy; df-selectivity + walker fuel are the two "think harder" knobs; hop-radius retired.

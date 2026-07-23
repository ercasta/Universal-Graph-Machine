# Derivation frame / the locality boundary (STEP A of the reactive-core arc)

> Status: DESIGN + first probe, 2026-07-23. Implements STEP A of the re-pointed arc
> (`implementation_plan.md` ▶ CURRENT ARC — LOCALITY BOUNDARY → REACTIVE CORE). Settles the forks the
> `bench/spike_derivation_frame.py` spike (GO 3/3) left open, and re-derives its Python shortcuts as an
> engine mechanism. Memory: `derivation-frame-consolidation`, `reactive-core-north-star`.

## The problem — locality of processing

Almost every grammar-route (flip) corner case is one class: a rule or a read touches graph it should not.
Three sub-cases, and it matters that they are DISTINCT:

1. **Token/entity dual-store** — a name resolves to a discourse TOKEN and an interpretation ENTITY; folded
   content lands on the entity, but a deferred recognizer (propositional-cause handle, hedge, comparison)
   interns by name to the token. Reasoning then reads the wrong node.
2. **Scaffolding leak** — a `who`/forward match enumerates an empty-named `ctrl=True` span/interpretation
   node that happens to carry a content edge.
3. **Control-mirror** — the same, on the FORWARD path, where `run_bank` keeps control nodes matchable by
   design (the schema meta-rule bound an interpretation control node).

Cases 2 and 3 are FACT-VIEW problems, already closed by a guard: `_facts_matching` emits `_guard`
(control+inert absent) on every bound node, and the forward path opts into the same via
`lowering.guard_fact`/`fact_only`. **This document is about case 1 — IDENTITY — which the guard does not
touch.**

### Where the dual-store actually bites (and where it does not)

The demand fetch `_facts_matching` resolves a bound endpoint through two Python resolvers:
`_candidate_nodes` (subject side) and `_bound_endpoint_ops`/`_endpoint_matches` (object side).

- A **name** endpoint resolves via `nodes_named(name)` → **every same-named node**. So a name-keyed query
  ALREADY reads the UNION of the token's and the entity's facts. This is why plain rule joins tolerate the
  split — chain joins by name (measured 2026-07-23).
- A **`ById` pin** resolves to **exactly one node**. So a NODE-BOUND fetch loses the union. The reify
  bridge (`?h subj ?s … ?s ?p ?o`) binds `?s` to the handle's subj-target NODE (a token) and then checks
  `?s ?p ?o` on that node only — missing the entity's content. THIS is the dual-store bite, and it is why
  propositional-cause needed the `intern_denoted` write patch.

## Two rejected approaches

- **Read-time single-hop denotes PICK** (the reverted slice-1c): resolve a bound node THROUGH `denotes` to
  the entity. It fixed prop-cause but **regressed comparative partial-order** — the comparison fact is
  authored on the TOKEN (deferred recognizer), so picking the entity LOSES it (`is cy more suspicious than
  bo` → unknown). A single hop trades one dual-store victim for another.
- **A materialized Python copy** (the spike's `project()`/`merge_back()`): a whole-graph read loop plus raw
  `add_node`/`add_relation`/`set_attr`. Proved the concept but is substrate-poking — a vision violation
  (`machine-semantics-are-isa-programs`). Must not ship.

## The design — canonical-equivalence-class UNION at the fetch endpoints

The fix both rejected approaches were groping toward: read a bound endpoint as its **canonical
equivalence class** — the node PLUS everything co-referent with it via the boundary relation, in BOTH
directions — and match the UNION, not a picked representative.

- Union (not pick) is exactly what does NOT lose the token fact: `class(cy) = {token_cy, entity_cy}`, so a
  fetch pinned to either sees BOTH the folded content and the token-resident comparison/hedge fact. slice-1c
  broke because it PICKED; union KEEPS.
- A **name** endpoint already unions (via `nodes_named`); this generalizes the SAME union to a **`ById`**
  pin, closing the one asymmetry that made node-bound fetches the dual-store's only victim.

### The frame is virtual — no second graph, no merge-back, no write-canonicalization

This is the key simplification the spike's eager copy hid. If READS union over the class, then:
- there is **no separate frame graph** to build — the "frame" is the equivalence class read as one logical
  node, materialized nowhere;
- there is **no merge-back** — nothing was copied out, so nothing merges in;
- **writes need no canonicalization** — a derived fact landing on the token OR the entity is read the same,
  so **`intern_denoted` becomes deletable** (its removal is a success metric, not a parallel task).

So "copy-on-lazy" reaches its limit: the copy is VIRTUAL (a read-time union keyed by canonical identity),
which is strictly better than a physical lazy copy — it needs no materialization, no memo invalidation, and
no merge boundary to get right. The one cost moves to the READ (walk the class per fetch); see Risks.

### The boundary relation

Reuse **`denotes`** as the canonicalization relation (token → entity), read in both directions to form the
class (`relations_from` for token→entity; `into` for entity→token). It is already the substrate's
token/entity link, already declare-before-use, and already what the reverted slice-1c and the surviving
`intern_denoted` both consult — so nothing new is introduced for the common case.

DEFERRED FORK: whether identity needs a DEDICATED relation (`<same-referent>` / `<canon>`) distinct from
`denotes` — e.g. if two ENTITIES are later found co-referent (cross-name `same_as`), or if `denotes`
acquires a reading where token and entity should NOT union. For now `denotes` is the class relation and
`same_as` (already in the substrate) is a candidate second class edge. Decide when a case forces it; do not
pre-build.

## Where it lives — one boundary, replacing N patches

Both consolidations the deeper diagnosis named live in the ONE fetch primitive `_facts_matching`:

- **fact-view (guard)** — ALREADY there (`_guard` on every bound node; `guard_fact`/`fact_only` mirrors it
  forward).
- **identity (canonicalization)** — ADD it to the endpoint resolvers `_candidate_nodes` (subject) and
  `_bound_endpoint_ops`/`_endpoint_matches` (object): a `ById` pin resolves to its class; an object pin
  matches any class member.

**A load-bearing detail the probe surfaced — REPORT UNDER THE ORIGINAL IDENTITY.** Expanding the class is
not enough. When a demand pins `?s`=n1 (token) and the match is found on a co-referent member n102 (entity),
the fetch must report the row as **(n1, …)**, not (n102, …) — because the demand solver confirms a bound
atom by checking the returned endpoints against the binding, and n102 ≠ n1 would be rejected. Canonicalization
means "n102 IS n1 for this purpose", so the fetch reports the DEMANDED identity and keeps the found node only
for a wildcard (None) endpoint. (In the probe this is one line; in the build it falls out of resolving the
pin to a class while the `emit` still echoes the passed endpoint — which `_facts_matching` already does for a
bound endpoint, so the in-resolver version inherits it for free.)

That single change retires the scatter: `intern_denoted` (write patch), and the pressure that produced the
reverted slice-1c and the reverted hedge `denoted=` patch. `resolve_write_node`'s denotation logic stays
(writes still prefer a real entity for tidiness) but stops being load-bearing for correctness.

## Vision-adherence

The identity DATA stays in the substrate (`denotes` edges authored by the fold). The resolver READS it —
the same category as `nodes_named` (a Python index read the vision already sanctions), not authoring. The
fetch PROGRAM (`_ISA_READER.match`) is unchanged ISA. This is NOT the spike's Python graph-authoring.

Purity refinement (DEFERRED): the class walk could itself be ISA `FOLLOW`s over `denotes` (out) and its
reverse, unioned as program variants the way `_facts_matching` already unions per candidate. Worth doing if
the resolver-vs-program line is later tightened; not required for correctness.

## Relation to the reactive core (why STEP A is the prerequisite)

A reactive trigger must fire into a BOUNDED, SOUND fact-view or it re-creates the locality bug with
side-effects. This fetch-level (guard + canonicalization) IS that view: every read the engine does already
routes through `_facts_matching`, so making it canonical-and-guarded gives the reactive core (STEP C) a
single, correct notion of "the facts about X" to react to — with no token/scaffolding to trip on. STEP A
delivers the boundary; STEP B gates firing; STEP C lifts the work-list onto both.

## Forks — resolved / deferred

| Fork | Resolution |
|---|---|
| Projection vs copy | Neither — a VIRTUAL union (read-time), no second graph, no merge-back |
| Boundary relation | Reuse `denotes` both-directions; dedicated `<canon>` deferred until a case forces it |
| Write canonicalization | Not needed (reads union); `intern_denoted` becomes DELETABLE (success metric) |
| Where it lives | `_candidate_nodes` + `_bound_endpoint_ops`/`_endpoint_matches` in `_facts_matching` |
| Resolver vs pure-ISA class walk | Resolver now (sanctioned, like `nodes_named`); ISA-FOLLOW refinement deferred |

## Risks / open questions (to close with the probe + build)

1. **Comparative NON-regression** — the whole reason to prefer union over pick. MUST re-verify the
   comparative partial order survives (`is cy more suspicious than bo` still `yes`, incomparable still
   `unknown`). The probe checks this first.
2. **Perf** — a class walk per bound-endpoint fetch. The class is tiny (usually {token, entity}); reverse
   `into` scan is the cost. If hot, index token↔entity at fold time. Measure on the suite time.
3. **Value-node interplay** — a `ById` pointing at a value-node already resolves by VALUE (`nodes_named(v)`)
   — itself a union; confirm canonicalization composes with, not double-counts, that path.
4. **Focus-scope membership** — `_facts_matching` tests `MEMBER((s,o), _FOCUS_LIVE)` by name; class members
   share the name, so membership is unchanged. Confirm.
5. **Self_as / cross-name coref** — if `same_as` is later folded into the class, its interaction with the
   demand-coref rules ([[coref-stays-cnl-not-engine]]) must stay CNL-driven, not hardcoded here.

## Probe

`bench/spike_derivation_frame_vision.py` — wraps the ONE fetch primitive `_facts_matching` to resolve each
bound endpoint to its `denotes`-class (both directions) and report under the original demanded identity, with
NO other change and NO graph-authoring (identity data stays in the substrate `denotes` edges).

**RESULT (2026-07-23) — GO.** CASE 1 (the node-bound reify bridge, handles authored UNPATCHED
`intern_denoted=False`): `is cat scared` is `no (assumed)` at baseline (the dual-store) and **`yes` with
canonical-class union** — the token/entity split dissolves at the fetch, no `intern_denoted`, no copy, no
merge-back. This confirms the design's core claim (virtual union at the fetch endpoints) and surfaced the
report-under-original-identity detail above.

**STILL OWED — the comparative NON-REGRESSION (the slice-1c discriminator) is a SUITE-level gate, not a
scratch probe** (a faithful comparative partial order needs the flip harness + corpus, not a bare
`declare_grammar`+`ingest` KB — the bare setup does not route the comparative QUESTION to `ask_comparative`).
The acceptance test for the BUILD: canonicalize in `_candidate_nodes` + `_bound_endpoint_ops`, then (a) the
shipped suite stays green — `test_comparative`, `test_world` partial-order, `test_facts_as_truth_bearers` —
and (b) the flip does not regress comparative where slice-1c did. Union should PASS both because it KEEPS the
token-resident comparison fact (it is a class member) where slice-1c's single PICK dropped it.

## Build — LANDED 2026-07-23

1. **`_candidate_nodes(ById entity)` → its `denotes`-class** (`chain._canon_class`, both directions —
   forward `relations_from`, reverse `into`). Handles the subject-drive loop and the object-drive
   single-bound path. Value-node pins (resolve by value) and names (`nodes_named`) unchanged; a skolem has
   no `denotes` so its class is {itself} (disambiguation preserved). Shipped suite flat (~84s → ~80s), so
   the reverse `into` scan is not a hot-path cost — no fold-time index needed yet.
2. **The both-bound object filter** (`_facts_matching` subj-bound branch): loop the object's class
   (`_bound_class_pins` — entity pin only; name/value-node/skolem stay a single filter, so the common path
   is byte-identical), report under the ORIGINAL demanded identity, dedup the co-referent overlap. Chose the
   loop-of-exact-pins over an ISA MEMBER test because MEMBER matches by NAME, which would over-match distinct
   same-named nodes and break skolem disambiguation ([[node-identity-is-not-a-semantic-proxy]]); the class
   must be a node-id set from `denotes` structure, nameless.
3. **`intern_denoted` DELETED** — the `MINT` field + machine branch (`machine.py`), the `assemble_facts`
   param (`lowering.py`), and the intake emit (`intake.py` now plain `assemble_facts`). The success metric:
   prop-cause gates green THROUGH canonicalization, not the write patch.

**RESULTS.** Shipped **973 green** (canonicalization + `intern_denoted` gone; suite time flat). Flip **43/930
— unchanged set** (no regression, no improvement): the identity cases were ALREADY green via the now-deleted
patches, so this is a CONSOLIDATION, not a flip-count mover — exactly as predicted ("measured by patches
deletable + forward==demand, not the flip count"). Comparative INTACT on shipped (`test_comparative` green)
— union kept what slice-1c's pick dropped. Prop-cause derives WITHOUT `intern_denoted` (gate + manual).

DEFERRED (unchanged): the dedicated `<canon>` relation, the ISA-FOLLOW purity refinement, and a fold-time
token↔entity index if the class walk ever shows on a profile. The next arc STEP (B/C) builds on this boundary.

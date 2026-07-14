# Name demotion & bridge retirement — design (Phase 2.3)

> **Status: IMPLEMENTED 2026-07-11 (A+B landed, 341 green).** Ratified then built the same day. The
> active plan is `implementation_plan.md`; this is the design detail for its Phase 2.3 ("`name` demoted
> to ordinary VALUED attr; value-accelerator indexes for KB-declared discriminating keys only"), which
> also retired the `TEMPORARY BRIDGE` dual-write. Companion substrate doc: `attrgraph.py`'s module
> docstring. See CHANGELOG for the as-built landing notes (incl. the two extra readers the design
> flagged as risks that indeed needed migration: `walker._successors`' `get_attr(r,"name")` and the
> `nodes_named(PREDICATE)` relation-finders; plus the garbage-triple cleanup `derived_triples` gained).

## Problem — the `TEMPORARY BRIDGE`

A relation node currently carries **two** representations of its predicate:

- the canonical **graded key** `{chase: 1.0}` (Phase 2.1, the neo-Davidsonian unification — the predicate
  is a category the rel node is a member of, seedable via `nodes_with_key`/`has_key`);
- a legacy **VALUED `name="chase"`** — the `TEMPORARY BRIDGE`, written at three sites
  (`attrgraph.add_relation`, `lowering.lower_rhs`, `lowering.to_attrgraph`).

The bridge was introduced (Phase 2.1) so the retired `rewriter.py` oracle — which read every relation's
predicate via `graph.name(rel)`/`nodes_named` — kept working. The oracle is gone (Phase 6.0), but the
bridge stayed because it turned out to be load-bearing for the LIVE engine, not just the oracle:

- **`derived_triples`** (the central triple reader) identifies a rel node as "a node with a VALUED
  `name`, ≥1 predecessor, ≥1 successor" and reads the predicate from that `name`. Drop the rel-node
  `name` write and it sees **no relations at all**.
- **`MINT.dedup`** finds an existing `subj -[pred]-> obj` via `g.name(r) == nm`.
- **~dozens of `g.name(rel)` predicate reads** across `apply`/`choose`/`decide`/`forms`/`surface`/…
  (≈52 `.name(...)` sites total — a mix of predicate reads and legitimate entity-name reads).

Entity nodes also carry VALUED `name` ("Paul") — that is legitimate and **stays**; only the *rel-node*
name is redundant. Two people named "Paul" stay distinct nodes; `name` is DATA under a key, never an
identity index (the label-less guarantee, `attrgraph.py` docstring).

## The A/B split

Phase 2.3 bundles two independent concerns:

- **(A) Predicate decoupling** — stop storing a rel node's predicate as VALUED `name`; read it from the
  graded key. *This alone retires the bridge.* Mechanical once one accessor exists; the prerequisite for
  a clean Phase 7(a) (don't intern-to-ints a store that dual-writes redundant predicate names).
- **(B) Entity-name demotion + KB-declared discriminating-key indexes** — `name` is currently a
  *privileged* hardcoded value-index (`_by_name`, "the ONE value index"). Generalize it to a declared
  facility: the engine offers `_by_value[key]` for **declared** keys, and `name` is declared by the
  production CONVENTION (not hardcoded in the engine). "Namelessness for real": no name-specific code
  path survives.

Both land this pass; (A) is the load-bearing half, (B) is behavior-neutral (name stays indexed by
default), so they compose cleanly and are gated together by the 341-test suite.

## (A) Predicate decoupling — spec

**Invariant (asserted):** a relation node carries exactly one **domain graded key** = its predicate
(non-reserved — not a `<…>` token — and not `confidence`). This already holds at every mint site
(`add_relation`, `lower_rhs`'s head MINT); (A) makes it the definition of "a relation's predicate."

1. **`AttrGraph.predicate(rid) -> str`** — returns that single domain graded key (or `""` if none).
   The predicate accessor replaces `name(rid)` for relations.

2. **`derived_triples`** — a rel node is now "has a domain graded key + ≥1 pred + ≥1 succ"; the predicate
   is `predicate(r)`. Subject/object still read VALUED `name` (they are entities). Memoization unchanged.

3. **`MINT.dedup`** — read the predicate from the graded key in `ins.attrs` (the non-reserved graded
   key), and match an existing relation with `g.has_key(r, pred)` instead of `g.name(r) == nm`.
   **`MINT.intern` is unaffected** — it canonicalizes *entity/token* literals via `nodes_named`, and
   entities/tokens keep their VALUED name; the key-aware guard (`finding-interning-aliases-predicate-
   literals`) stays.

4. **Drop the three bridge writes:**
   - `add_relation` mints `add_node({rel_name: graded(1.0)}, …)` — no VALUED name. Control-ness via the
     `control=` param as today.
   - `lower_rhs` head MINT `attrs = {pred: graded(1.0)}` — drop `{name: valued(pred)}`.
   - `to_attrgraph` post-pass: for a rel node (pred && succ), ensure the graded key and **remove** the
     VALUED `name` (entities keep theirs).

5. **Reader flip** — classify each `g.name(x)` site: a relation's-predicate read → `g.predicate(x)`;
   where it is a *test* against a known predicate (`g.name(r) == "add"`), the cleaner `g.has_key(r, "add")`;
   an entity-name read stays `g.name(x)`. (Per-site judgment; the suite gates every one.)

6. **Reserved-key collision, resolved for free** — dropping the rel-node VALUED write means a relation
   whose predicate is literally `name` just carries `{name: graded(1.0)}`, distinct in *kind* from an
   entity's `{name: valued(...)}`. The current special-case guard (skip the graded dual-write for a
   `name` predicate) is deleted. The one requirement: the value-index sync must fire only for VALUED
   `name`, never a graded `name` key — which (B)'s generic rule below gives us uniformly.

## (B) Declared discriminating-key indexes — spec

Generalize the single hardcoded `_by_name` into a declared facility, behavior-neutral by default.

1. **`_by_value: dict[key, dict[value, set[nid]]]`** — a value-index maintained for **declared** keys
   only, replacing `_by_name`. Sync rule (one place, in `set_attr`/`remove_node`/`copy`): index `nid`
   under `_by_value[key][value]` iff `key` is declared **and** the attr is **VALUED**. (Graded keys —
   including a `name` predicate — are never value-indexed; they live in `_by_key`.)

2. **`AttrGraph(schema=None, indexed_keys={"name"})`** — the declared set. Default `{"name"}` is the
   production CONVENTION (seed-from-ground anchors entities by name), now expressed through the general
   mechanism rather than a hardcoded `if key == NAME`. A schema/KB may declare additional discriminating
   keys (e.g. a domain id / signature). `declare_index(key)` adds one and back-fills existing nodes.

3. **Public API:** `nodes_with_value(key, value) -> list[nid]` (candidate set, never resolves —
   the label-less guarantee), `value_count(key, value) -> int` (df for seed selectivity). `nodes_named`
   / `name_count` become thin wrappers over these for the `"name"` key (call-site-compatible), so no
   reader outside the substrate changes for (B).

4. **Demotion = no name-specific code path.** The `if key == NAME` blocks in `set_attr`, `remove_node`,
   and `copy` are deleted, replaced by the generic declared-key sync. `name` is no longer privileged in
   engine code — only declared by convention.

## Migration plan

1. Add `predicate()`, `nodes_with_value`/`value_count`, `declare_index`, `_by_value` + the generic sync;
   make `nodes_named`/`name_count` wrappers; default `indexed_keys={"name"}`. (Behavior-neutral so far —
   the bridge still writes rel-node names.)
2. Flip `derived_triples` + `MINT.dedup` to the predicate-key path.
3. Drop the three bridge writes; delete the reserved-key-collision special cases.
4. Sweep the `g.name(rel)` predicate readers → `g.predicate`/`has_key` (per-site).
5. Run the full suite after 2–4; it differentially gates `derived_triples` and every reader.

## Risks

- **A missed predicate reader** silently reads `""` after the bridge drops. Mitigation: step 1–2 are
  behavior-neutral, so a failure after step 3 localizes to "a reader still on `name`." The suite (esp.
  `test_isa_lowering`, `test_isa_runbank`, reasoning-parity, surface/render tests) exercises the readers.
- **The single-domain-graded-key invariant** — if any site EMITs an extra graded attr onto a rel node,
  `predicate()` is ambiguous. Audit at implementation; none is expected (embeddings live on entities).
- **`to_attrgraph`** bridges a recognition `Graph` → reasoning `AttrGraph`; its rel-node name removal
  must run after edges are copied (rel-ness is topological). Low risk, localized.
- **Performance** — `_by_value` is the same shape as `_by_name`; no regression. Phase 7(a) later interns
  this settled representation.

# Design — hardcoded same-name INTERNING (CNL reader)

Status: **design, not built.** Supersedes the rule-based coref plan (value-indexing + defeasible
node-coalescing) that previously filled this file — see git history and
`docs/demand_driven_coref_plan.md` for the investigation and perf data that led here. This is a
**major simplification** decided in conversation.

## Decisions log (2026-07-13)
- **Reverted** the uncommitted demand-driven change set (`git restore --staged --worktree ugm/ tests/`);
  every piece was superseded (chain.py `same_as`-visibility → pointless with no `same_as`; graded rule
  `same_as`-follow → wrong once declaration & use-site unify; deferred `prop` → machinery being deleted;
  test relaxations → revert naturally). Building interning on the fast committed base `550e11f`.
- **No `[new]` modifier.** Distinct same-name referents in CNL are disambiguated by using a **distinct
  name** (`other_alice`). No new syntax.
- **Cross-name coref** (`the thief` = `cy`, pronouns) is **future work** — out of scope here.
- **Stopwords**: the CNL doesn't really have stopwords; ignore the over-marking/stoplist cleanup for now.
- **Indexing** (old Part A) is being pursued **separately** as a general (non-coref) feature — the user
  sees value across the system (system-1 associative recall, the code-reasoning project). To be designed
  in its own doc; no longer coupled to the coref fix.

## The move (one paragraph)
Stop deciding coreference with rules. Same-name mentions are **one node by construction**: in the CNL
reader, on recognizing a mention named `n`, REUSE the existing node for `n` instead of minting a fresh
one ("hardcoded strategy to coalesce as we go" — the user's phrase). If an author means a *different*
referent, they give it a **distinct name** (`other_alice`). So **sameness is the mechanical default;
distinctness is a distinct name.**

This is the polarity inversion of the old plan: not *prove-same* (fire a `same_name` rule → M²
Cartesian → propagation), but *presume-same by name*.

## Why this is the right shape
- Kills the **M² `same_name` Cartesian** — there is no `same_name` rule; nodes are born canonical
  (O(1) dict lookup per mention).
- Kills **propagation** (`same_as_rules`) — one node per entity, so there is nothing to copy across.
- Kills **B6's lossy `SPLIT`** for same-name coref — distinctness is declared UP FRONT (`[new]`), never
  discovered after merging, so we never coalesce-then-retract on this path.
- **Blocker B (graded declarations) vanishes** — `bright is gradable` and the use-site `bright` are the
  SAME node; the graded rule reads `gradable` locally with no `same_as` hop. Same for
  `closed world`/`disjoint` markers.
- The whole demand-driven working-tree change set becomes **dead** (no `prop` to defer, no `same_as` to
  make matcher-visible) → revert it and build on `550e11f`.

## Two entry paths, two identity policies (the key boundary)
Interning is a **CNL-front-end policy, NOT a graph primitive.** The graph's node-creation stays
identity-explicit; interning is applied only by the CNL reader.
- **CNL intake** (`_recognize`/`ingest`) — natural-language authoring. "Same surface name ⇒ same
  referent" is the right *intake heuristic* here; interning lives HERE. Opt out by using a distinct
  name (`other_alice`).
- **Programmatic producers** (e.g. `../pystrider` code-reasoning, [[ugm-code-reasoning-project]]) — the
  producer KNOWS the scope, so it mints distinct nodes DIRECTLY via the graph/ISA API (a variable is a
  node keyed by `(scope, name)` or a fresh id; the `SUPPOSE`-tree already has scoped environments). It
  never emits ambiguous same-name mentions expecting the engine to reconcile them, and never touches
  CNL interning. The engine must NOT force interning on this path.

## Vision reconciliation (`coref-stays-cnl-not-engine`)
The matcher stays **coref-free**: there is one node per referent, so nothing for `_facts_matching`/the
matcher to follow — no union-find, no coref-following (the memory's actual red line). And because
interning is confined to the CNL reader (above), the **engine below it does no coref at all** — a
CLEANER satisfaction of the vision than rule-based coref was. What changes is only that the coref
*decision* moved from fire-able rules to the CNL reader's naming policy (same name ⇒ same; distinct name
⇒ distinct). "Coref is declarative; the engine never follows coref" is PRESERVED. Confirmed by the user.

---

# Mechanism

## M1. Name-interning in the CNL reader
The substrate already indexes names: `attrgraph._by_value[NAME]` / `nodes_named` (`machine.py:376`).
In the CNL reader ONLY (`authoring._recognize` + mid-session `ingest`), when a mention with surface
name `n` is recognized: if a node named `n` already exists, REUSE it; else mint one. Eager and cheap
(no pass, no rule). The graph's own node-creation primitive is UNCHANGED (identity-explicit) so
programmatic producers are unaffected (see two-path boundary above).

## M2. Distinct referents → use a distinct name
If an author genuinely means a different `alice`, they **name it differently** (`other_alice`) — no new
syntax, and it forces referential clarity (a mild, arguably good constraint in a session-sized working
set). Programmatic producers don't even need that — they mint distinct nodes directly (two-path
boundary above).

## M3. Stopwords — deferred
Per the Decisions log, the CNL doesn't really have stopwords; the over-marking/stoplist cleanup is
ignored for now. (Interning also collapses any incidental duplicate tokens to one node, so the M²
blowup is gone regardless.)

## M4. Defeasibility — authored, not inferred
Same-name distinctness is authored via `[new]`; there is no post-hoc `SPLIT`. If an author forgets
`[new]` for two genuinely-distinct same-name entities, that's an authoring error fixed by re-authoring,
not engine auto-recovery. This is the honest, simple contract and the reason the design collapses so far.

---

# What gets DELETED / SIMPLIFIED
- `same_name_coref_rules` (`universal.py`) — replaced by interning.
- `same_as_rules` / `_coref_propagation` (`authoring.py`) and the eager `run_bank(kb, coref+prop)` coref
  pass in `load_corpus`/`load_facts` — gone (nothing to propagate).
- `same_as` **consumers** simplify or disappear: `focus.py:251` same_as skip; `chain._same_as_neighbors`
  / `_one_identity` / `resolve_write_node` write-target disambiguation (one node per name → the
  name→one-node ambiguity dissolves). Do this deliberately with the suite as guard.
- The uncommitted demand-driven working-tree changes — **revert** (`git restore ugm/ tests/`; Q4).

# What STAYS / is reused
- `mark_mentions` — still marks what's a mention/entity (drives interning eligibility); tighten it (M3).
- `COALESCE`/`SPLIT` opcodes — ONLY relevant to **cross-name** coref (`the thief` = `cy`, pronouns),
  which interning can't do. Keep OUT of this change; if wanted later, it's an opt-in rule→`COALESCE`
  (and only THAT path might ever need `SPLIT`). Not v1.
- Value-indexing (old Part A) — demoted to a **general** value-match optimization (graded closeness and
  other keys); off the coref critical path now. Optional, later.
- `propagate_embeddings` — graded-layer union tool; keep.

# Blocker A / B / C (from the demand-driven plan) — status
- **B (graded)**: gone (M1 makes declaration and use-site one node).
- **A (unbound NAF) / C (forward materialization)**: moot — those were artifacts of *deferring* `prop`.
  We don't defer; we intern eagerly and cheaply, so there is no `prop` and no deferral.

---

# Implementation order (each step ends green)
0. **DONE — reverted** to `550e11f` (Decisions log).
1. **DONE — interning.** Implemented as `forms.intern_mentions` (+ `_fold_node`), called in
   `load_corpus`/`load_facts` right after `mark_mentions`. HOOK NOTE: not at `tokenize` (which mints one
   node per word and can't tell a rule variable `?c` from an entity yet) but **after `mark_mentions`**,
   which already scopes the eligible set to `<mention>`-marked entities (excludes `?vars`/`<control>`/
   predicates). It folds same-named mention nodes into one (rewire each reified relation's endpoint,
   union embedding dims, drop victim). The old coref pass is left in place; it now fires trivially (no
   duplicate mentions to link) — Step 2 removes it. **Result: 338/338 green; demos 4-8x faster**
   (01 2.4→0.5s, 03 13→2.0s, 04 39→4.7s, 05 62→10s). Answers unchanged incl. graded/defeasible `why`
   (Blocker B is gone — declaration & use-site are one node).
2. **DONE — removed the dead coref pass.** Deleted only the AUTOMATIC same-name coref invocation in
   `load_corpus`/`load_facts` (the `run_bank(kb, coref+prop)` pass and the `+coref+prop` appended to the
   returned rules). The coref FUNCTIONS stay (`same_name_coref_rules`, `same_as_rules`,
   `_coref_propagation`, `SAME_AS_RULES`, `propagate_embeddings`) — they are live TOOLS used by five test
   files for ASSERTED identity and are the mechanism the future cross-name coref will reuse; only their
   auto-run at load was dead. **338/338 green; demos faster again** (04 4.7→2.3s, 05 10→2.5s; ~17-24x
   over baseline).
3. **SKIPPED (by design) — the `same_as` consumers are NOT dead.** `resolve_write_node`/`_one_identity`/
   `_same_as_neighbors` and the `focus.py` `same_as` skip are general write-target discipline for the
   PROGRAMMATIC path (EMIT / SUPPOSE pencil / `ById` — the "two Pauls" case where same-name duplicates
   legitimately persist) and for ASSERTED `same_as`. Step 3's premise ("one entity node => ambiguity
   dissolves") holds only for the CNL path; duplicates persist on the programmatic path, so these
   consumers must stay. Deleting them would break suppose/ById. No change made.

# Open questions for the user
All prior open questions are resolved — see the Decisions log at the top. Remaining detail to settle
during implementation: the exact hook point in `authoring._recognize`/`ingest` where a recognized
mention consults `nodes_named(n)` to reuse-vs-mint, and confirming nothing downstream depends on
duplicate same-name mention nodes existing (the `same_as` consumers listed above are the audit set).

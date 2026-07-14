# Phase A — Python as firmware over ISA: the demand matcher (A1)

> **Status: IN PROGRESS (2026-07-14).** The first, differential-gated increment of Phase A / A1
> (`docs/design/rust_engine_plan.md` §2) has LANDED as an ADDITIVE parallel path — the bespoke demand
> matcher stays the reference oracle; the shared-ISA-matcher path is proven equal on every call
> under a cross-check flag. The production SWAP (retire the walk) is the user's ratified gate and is
> NOT taken here.
>
> Prerequisite reading: `docs/design/rust_engine_plan.md` (§2 A1–A5), `docs/attic/isa_control_machine.md`,
> `ugm/chain.py` (`_facts_matching` — the procedure), `ugm/lowering.py` / `ugm/machine.py` (the ISA
> matcher the forward path already uses).

## 0. What A1 is, in one screen

Today there are TWO matchers:
- the **forward** matcher — `Machine.match` over a `lower_conj` program (SEED/FOLLOW/TEST/JOIN/…),
  used by `run_bank` and `match_pats`;
- the **demand** matcher — `chain._facts_matching`, a hand-written topology walk (walk OUT of a bound
  subject / INTO a bound object / a whole-predicate scan), plus a Python `env` dict threaded across
  body atoms in `_solve_demand_rule`.

A1's thesis: **the demand path's per-atom fact lookup is the SAME topology walk the ISA matcher does**
(SET the bound endpoint node → FOLLOW to the rel → TEST the predicate key → FOLLOW to the other
endpoint). Route it through `Machine.match` and the second matcher DIES — forward and demand unify on
one matcher, which is the precondition for a single Rust interpreter (Phase B) to run both.

## 1. The crux: the demand path carries visibility POLICY the forward matcher does not

`_facts_matching` is not just a walk. It bakes in three visibility filters that the pure forward
matcher (SEED/FOLLOW/TEST + `skip_inert`) has no notion of:

1. **Fact-layer visibility.** A demand read sees only real FACTS: it skips CONTROL and INERT
   endpoints and rels — reified rule/frame scaffolding, provenance (`<j:>`/`uses`/`proves`), coref
   `<mention>` markers. The forward matcher skips only *inert* (`skip_inert`), and avoids control by
   predicate-key seeding; it has no endpoint control-skip.
2. **SUPPOSE scope pencils.** A CONTROL rel tagged with the ACTIVE `<hypothesis>` scope IS visible
   inside that scope (`_rel_in_scope`) — the pencil a SUPPOSE branch reasons over. This is a *runtime*
   parameter (`scope`), not a graph property.
3. **Focus attention.** A fact is in play iff an endpoint is in the focus working set
   (`focus_scope`) — bounded attention (§8.3b). Also a *runtime* set, not graph structure.

Plus a substrate detail that is EASIER on the ISA side, not harder: a FREE slot returns the
discovered node as `ById(node)` (the id-addressed core, Stage 3) so distinct same-named nodes stay
distinct bindings. The ISA register file already holds node ids, so this is native — the matcher
binds a reg to the specific node; the wrapper just wraps it `ById`.

**So the walk decomposes into (a) a topology walk that IS ISA-structural + (b) three visibility
filters that are runtime policy.** (a) moves to the shared matcher; (b) is the irreducible demand
policy A5 must name.

## 2. The fork (the load-bearing decision — the user's call, for the SWAP)

> **RESOLVED 2026-07-14 by dissolution — see `docs/attic/firmware_over_isa_design.md` (the LOCKED design).** The
> fork below (a Machine `visible(nid)` predicate vs. driver post-filters) is superseded: the ratified
> principle is NO PRIVILEGED PARTITIONS (no kind-flags, no separate rule graph). A "fact read" is a lowered
> PROGRAM with a COMPILER-EMITTED attribute guard + optional register-pointed live-set (focus restricts,
> scope extends). Neither "fork" survives as such; the matcher stays dumb and visibility is expressed in the
> lowered read program. The fork text is kept below only as the reasoning trail that led there.

How should the three policy filters live once the walk is the ISA matcher?

- **Fork (a) — a `visible(nid)` predicate on the Machine.** Generalize `skip_inert` into a per-run
  candidate-visibility callback the matcher consults at SEED/FOLLOW candidate time. The demand path
  passes `visible = fact-layer ∧ (scope pencil) ∧ focus`; the forward path passes the inert-skip.
  *Pro:* the matcher does ALL filtering; the demand path becomes purely "build the atom program + a
  visibility predicate"; genuinely one matcher. *Con:* it puts policy-carrying capability into the
  core and TOUCHES the to-be-frozen instruction-set/interpreter contract (Phase B must port a
  closure boundary; determinism trap §4.2 of the Rust plan). A closure per candidate is also the
  Rust FFI hot spot to avoid.
- **Fork (b) — the matcher stays dumb; the demand DRIVER post-filters.** The ISA matcher does the
  SET/FOLLOW/FOLLOW walk (candidate binding), and the demand wrapper applies the three filters to the
  matched states. *Pro:* the core stays pure (no policy in the contract); Phase B ports an unchanged
  matcher; the filters are a small, named, Rust-portable predicate set (A5). *Con:* the wrapper still
  holds three Python filters — the unification is of the JOIN/topology, not (yet) of visibility.

**This increment implements fork (b)** — it is valuable under EITHER outcome (fork (a) later just
moves the same three post-filters into a `visible` callback) and, crucially, does NOT touch the
instruction-set contract the plan says to freeze first. The recommendation to the user for the
eventual swap: **fork (b)**, because the Rust-plan guardrails (keep the matcher dumb + portable, no
per-candidate Python callback across the FFI) point that way, and the three filters are exactly the
"minimal irreducible PRIMITIVES" A5 is meant to isolate — scope/focus are seed-set/candidate-set
restrictions, and fact-layer visibility is a node-flag test that becomes a cheap Rust predicate.

## 3. What landed here (additive, oracle-retained)

- `chain._facts_matching_isa` — the single-atom demand lookup with the topology walk done by the
  SHARED ISA matcher (`Machine.match` over `SET`/`FOLLOW` / a `SEED`-by-predicate-key wildcard scan),
  and the three visibility filters as post-filters (fork (b)). Free slots wrap to `ById`, exactly the
  walk.
- `chain._facts_matching` is now a thin dispatcher: it returns the bespoke walk
  (`_facts_matching_walk`, the reference oracle) and, when `chain._CROSSCHECK` is set, asserts the ISA
  path agrees on that call (order-insensitive multiset compare) — the differential gate.
- `tests/test_isa_demand_matcher_differential.py` flips `_CROSSCHECK` on and drives the real demand
  procedures (`check`/`chain_sip`/`suppose`) over banks exercising every shape: bound-subj/wildcard,
  bound-obj/wildcard, both-bound, whole-predicate, NAF (nested negative subgoals), coref `same_as`,
  SUPPOSE scope pencils, focus attention, and `ById` endpoints — so every internal `_facts_matching`
  call in those closures is cross-checked against the ISA matcher.

Production is UNCHANGED (the oracle path runs; `_CROSSCHECK` defaults off), so the suite stays green
on the shipped behaviour while the ISA path is proven equal by the differential sweep.

## 4. Remaining A1 (after this increment) — the actual swap + the join loop

- **A1-swap (user gate).** Flip `_facts_matching` to return the ISA path; delete `_facts_matching_walk`
  once the suite + sweeps are green on it. Decide fork (a) vs (b) for where the three filters live.
- **A1-join / A2.** The bigger half: the per-atom SIP JOIN loop in `_solve_demand_rule` (the `env`
  threading that INTERLEAVES sub-demand raising with evaluation) becomes a whole-body `Machine.match`
  seeded from the demand's bound endpoints, with the `env` = `State.regs` (A2). The subtlety the plan
  flags: the magic-set sub-demand raising is currently interleaved per atom under the partial env
  (SIP), so a straight whole-body match must still raise the same scoped sub-demands — this is where
  the coref fan-out / `ById` / focus semantics must survive, and is the real intellectual care of A1.
- **A3/A4/A5.** graded/value/coref → existing GRADE/VMATCH/coref-rule opcodes; the demand loop + NAC
  as a control-machine program; isolate + name the irreducible PRIMITIVES (fact-layer visibility,
  scope pencil, focus — and `_find_skolem_witness` structural re-finding).

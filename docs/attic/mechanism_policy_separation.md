# Mechanism / Policy Separation in the ISA — Probe 1: copy-on-delete retraction

> **Status:** ✅ **DONE / Probe 1 built (2026-07-14).** Copy-on-delete retraction is live: `RETIRE`
> opcode (privileged, ungated by lowering), `record_history` (in-graph meta-visible archive that
> retains provenance), the `retract` driver (decide → record → retire), and `resurrect`. All slices
> §5.1–§5.6 landed; acceptance §6 met. Suite: **350 passed** (346 baseline + 4 net-new). Axis B (§8)
> remains the untouched second probe. Below is the design as executed (kept as the record).
>
> **What shipped vs. the OPEN calls (smallest-interpretation choices):** `RETIRE(rel)` (not
> `DROP_FACT_EDGE`) — matches the unit retraction operates on. Gate = "only the driver assembles
> `RETIRE`" (no `privileged=True` flag) — asserted by `test_no_rule_lowering_emits_retire`. History =
> a new inert `<history>`/`was_subj`/`was_obj`/`was_pred` record (not the `<j:>` vocabulary) that
> references the surviving entities via DISTINCT meta-predicates so it does not alias the live fact;
> provenance is RETAINED by redirecting the retired rel's inert `proves`/`uses` edges onto the record.
> `INTERPOSE_RULE` was removed from the TMS (not just from `RETRACT_RULES`); the `INTERPOSE`/`RESTORE`
> opcodes + `lower_rewire` stay for their own direct tests (§7 defers their removal). One real bug
> found + fixed: `seed_retract`'s `targets` node was a non-control predecessor of the rel node and
> could be misread as the subject — it is now control-stamped and the subject/object finder excludes
> control+inert.
>
> **For a fresh session:** read this doc, then `ugm/retraction.py`, the `RETIRE` opcode in
> `ugm/machine.py`, and `tests/test_retract_rules.py`. Standing rules: **no commits by the assistant**;
> domain logic only in banks; correctness before performance.

---

## 1. The thesis (why this probe exists)

A lesson from kernel design: **never conflate mechanism with policy.** The kernel provides raw
mechanisms (the MMU translates addresses); higher layers impose policy (which pages a process may touch).
The UGM ISA currently violates this in two places — it bakes *policy* into *structure*:

- **Axis A — fact-monotonicity is baked into the opcodes.** `DROP_CTRL` *refuses* to delete a fact edge
  (raises `ControlEdgeError`); the only sanctioned fact-edge mutation is `INTERPOSE`, a reversible splice
  that exists *solely because raw deletion is forbidden*. "No fact is ever deleted" is enforced as an
  opcode refusal, not as a policy a layer imposes.
- **Axis B — control-vs-fact is baked into nodes.** `is_control` flag + the `<…>` naming convention mark
  nodes that are really *machine state* (`<call>`, `<demand>`, `<focus>`, `<hypothesis>`) living in the
  data graph. (Axis B — lifting execution/control state into machine *registers/pointers* instead of data
  nodes — is the **second probe**, sketched in §8; NOT in scope here.)

The kernel-correct shape: the ISA offers **raw mechanism** (delete), and monotonicity/provenance become
**policy expressed as programs**, guarded by a **privilege** gate so ordinary reasoning can't wield the
mechanism. The honest form of "allow deletion" is *not* "delete freely" — it is "raw delete exists, but
only sanctioned policy code emits it." Without the gate you don't separate mechanism from policy; you just
remove the guardrail.

**HARD CONSTRAINT — explanation is DATA, in the graph, matchable (ratified with the user).** Provenance /
`why` / history must stay first-class MATCHABLE nodes in the SAME graph — that is *why* the retraction
cascade can be rules over `proves`/`uses`, and it is what lets the system **reason about its own reasoning**
(reflection / meta-rules / TMS). Do NOT move explanation to a separate sidecar/plane — that would kill
meta-reasoning. The "planes" in this doc are **logical visibility scopes** (ordinary reasoning sees current
facts; meta-reasoning sees provenance/history — the existing inert/meta discipline), NOT separate graphs.
The ONLY thing that physically leaves the graph is non-explanatory *execution* state (Axis B, registers).

**What this probe actually buys (perf is NOT the driver):**
1. It retires the `INTERPOSE`/`RESTORE` **zombie** — today a retracted fact isn't removed, its relation is
   *rerouted through a `<retracted>` marker* and left in place (a broken-but-present spliced relation).
   Copy-on-delete replaces that with a clean **(real deletion of the live relation edges) + (an explicit
   historical record asserted as reasoned-over data)**. The live fact genuinely stops existing as a
   relation; the history is honest first-class data, not an in-place splice hack.
2. It makes fact deletion a **real, privileged mechanism** — the foundation a later **GC/forgetting policy**
   reuses to actually shrink the graph (remove history nothing, not even meta-reasoning, still references).
   That GC is where the inert-accretion perf risk is genuinely addressed; this probe only *enables* it.
   (Day-to-day accretion cost is bounded by **focus / attention**, not by exiling explanation.)

**Temporal refinement (the crux for soundness).** Monotonicity is not purely policy — the demand chain's
memoization and NAF/CWA soundness *assume* facts don't vanish mid-reasoning. So the correct line is
**temporal**, not "delete is now free":
- **within a reasoning pass** → monotone is *mechanism* (no deletion mid-fixpoint);
- **between passes** → deletion is *policy* (retraction / GC / forgetting), privileged, copy-on-delete.

Retraction is already a between-passes operation (`retract()` runs its own fixpoint, separate from
reasoning). This probe keeps it there. It must NOT make deletion reachable from ordinary reasoning rules.

---

## 2. What exists today (ground truth)

- **Retraction is rules** (`ugm/retraction.py`). `retract(graph, rel)` seeds `<retract> targets rel`,
  then runs `RETRACT_RULES` to a fixpoint:
  - `CASCADE_RULE` (`tms.cascade`): propagates the retract marker along `proves`/`uses` provenance to
    every dependent fact (aggressive single-support form; stratified; won't touch an `<axiom>` base fact).
  - `INTERPOSE_RULE` (`tms.interpose`): `rewire=[("cut","?rel","?o"),("link","?rel","<retracted>?"),
    ("link","<retracted>?","?o")]` — splices an inert `<retracted>` marker into the fact's 2-hop path so
    `?rel`'s successor is now the marker, not `?o`. The matcher (which skips control/inert) stops seeing
    the fact. The `?rel` node **stays** (its `proves` provenance survives). Reversible via `RESTORE`.
- **`INTERPOSE`/`RESTORE` opcodes** (`ugm/machine.py`): the reversible splice + its exact inverse.
  `lower_rewire` (`ugm/lowering.py`) is the ONLY producer of `INTERPOSE`, and retraction is its ONLY user.
- **`DROP_CTRL`**: deletes a bare edge, but raises `ControlEdgeError` on a fact edge — the structural
  refusal that enforces monotonicity.
- **Provenance** (`ugm/provenance.py`): `<j:KEY>` justification nodes with `proves -> fact` and
  `uses -> premise` edges; inert. A fact's rel node is the target of `proves` edges.
- **Matching skips inert/control** (`run_bank`/`_facts_matching`), which is *why* a hidden fact and the
  `<j:>`/`<retracted>` scaffolding coexist — and *why* the graph accretes.
- **Tests pinning current behavior** (`tests/test_retract_rules.py`): `test_cascade_hides_the_whole_chain_
  below_a_retracted_base`, `test_cascade_mints_no_new_justifications`, `test_interposition_preserves_
  relation_identity`, `test_no_retract_no_effect`. Also `tests/test_isa_interpose.py`, `tests/test_rewire.py`
  test the `INTERPOSE` opcode directly (these stay — the opcode isn't removed, retraction just stops using it).

---

## 3. The probe

**Goal.** Retraction *really deletes* the fact (and its dependents) from the **live graph**, copying each
pre-image into a **separate history archive** first, so:
- the live graph carries **no `<retracted>` accretion** (the retracted structure is gone, not hidden);
- resurrection re-materializes a fact from the archive (the `RESTORE` role, now archive→live);
- the deletion **mechanism is privileged**: ordinary reasoning rules cannot emit it.

**Three cleanly-separated steps (the mechanism/policy split made concrete):**
1. **Decide** (reasoning, read-only): the CASCADE finds the full set of rel nodes to retract by traversing
   `proves`/`uses` provenance — unchanged, still rules. This is the "what to delete" question; it stays in
   the reasoning layer and touches nothing.
2. **Archive** (policy): for each rel in the set, copy its pre-image — the reified relation
   `s -[rel]-> o`, the rel's attrs, and its provenance edges (`<j:> proves rel`, `<j:> uses …`) — into the
   history archive. (MINT-into-archive; this is where copy-on-delete's "copy" lives.)
3. **Retire** (privileged mechanism): delete the live edges (`s->rel`, `rel->o`) and the rel node. This is
   real fact deletion — the raw mechanism, emitted only by the retraction policy.

**The privilege gate (recommended, minimal).** The fact-deletion op is **not in the rule→program lowering
vocabulary** — `lower_rhs`/`lower_rewire`/etc. never emit it. Only the retraction (and later GC) **policy
driver** assembles a program containing it. So ordinary reasoning rules *structurally cannot* delete a
fact (soundness-by-construction preserved for reasoning), while the policy layer wields real deletion. A
test asserts a rule cannot produce the op. (OPEN: whether to also add an explicit `privileged=True` rule
flag — recommend NOT for the probe; "only policy drivers emit it" is a cleaner, smaller gate.)

**The history/pre-image stays IN the data graph as meta-matchable data — NOT a sidecar.** (This corrects an
earlier draft that recommended a sidecar `AttrGraph`; that was wrong — see the HARD CONSTRAINT in §1.)
Retraction records the pre-image as **explicit historical data** in the same graph, visible to
meta-reasoning (the inert/meta visibility discipline) so the system can still reason *about* what it used to
believe and why it was retracted. What is *deleted* is the LIVE relation's matchability by ordinary
reasoning (its live edges), replacing the `<retracted>` splice. What is *retained* is the historical record
+ provenance, as reasoned-over data. Graph *shrink* is not this probe's job — it's a later GC policy.

---

## 4. Concrete design

### 4.1 The mechanism: a privileged fact-deletion op
Add one effect opcode to `ugm/machine.py`, e.g. **`RETIRE(rel)`** (name negotiable):
- Semantics: remove the bare edges into and out of `regs[rel]` (subject->rel, rel->object) and remove the
  rel node itself. Unlike `DROP_CTRL`, it does NOT refuse a fact edge — deleting a fact edge is its purpose.
- It is the raw mechanism. It carries no archiving (archiving is policy, step 2 — do NOT bake copy-on-delete
  into the opcode, or you re-conflate mechanism and policy). The opcode just deletes.
- OPEN: `RETIRE(rel)` (delete the whole reified relation given its rel node) vs a lower-level
  `DROP_FACT_EDGE(a,b)` (delete one fact edge, privileged). Recommend `RETIRE(rel)` — it matches the unit
  retraction actually operates on (a relation), and keeps the op count minimal.

### 4.2 The historical record (IN the data graph, meta-matchable)
The pre-image is recorded as **explicit historical data in the same graph** — NOT a sidecar (see §1 HARD
CONSTRAINT). Before retire, assert a first-class historical record that meta-reasoning can match:
- the fact that used to hold (its subject/predicate/object) and that it was retracted (by what, if known) —
  e.g. a `<history>`/`<was>`-style record with its own relations, in the **meta-visible** scope (inert to
  ordinary matching, visible to meta-rules — the existing discipline);
- the provenance (`<j:>` with `proves`/`uses`) for the retracted rel, retained as reasoned-over data so a
  resurrected fact restores its justification and so the system can still answer "why did we retract this?".
- OPEN: exact shape of the historical record (reuse the `<j:>`/provenance vocabulary vs a new `<history>`
  record). Recommend the smallest shape that (a) stays meta-matchable and (b) carries enough to resurrect.
- Step ORDER matters: the cascade READS `proves`/`uses` to decide the set; retire DELETES the live relation
  edges. Finish the **decide** phase before the **retire** phase — decide → record → retire — or the cascade
  loses its footing mid-run. (Recording is additive/meta; retire removes only the LIVE relation's ordinary
  matchability. Provenance the cascade still needs stays matchable throughout the decide phase.)

### 4.3 The retraction driver (replaces INTERPOSE_RULE)
`retract(graph, rel)` becomes a policy operation over the ONE graph:
1. Run `CASCADE_RULE` to fixpoint to accumulate the `<retract> targets ?rel` set (unchanged — reasoning).
2. Read the target set from the graph.
3. For each target rel: assert its **historical record** (meta-visible), then assemble+run a `RETIRE(rel)`
   program (privileged mechanism) to delete the LIVE relation edges.
- `CASCADE_RULE` stays. `INTERPOSE_RULE` is **removed** from `RETRACT_RULES`; retire replaces it. The
  `<retracted>` marker vocabulary is no longer used by retraction (the opcode `INTERPOSE`/`RESTORE` remain
  in the ISA for their direct tests, just unused by the TMS).

### 4.4 Resurrection (the RESTORE role)
`resurrect(graph, rel_key)`: re-materialize a fact from its (in-graph) historical record back into the live
graph — re-intern endpoints via the ISA (`lowering.assemble_facts`, the vision-aligned fact-build path) and
restore provenance. This replaces `RESTORE`-based un-hiding for retraction. Because the history never left
the graph, this is a read-of-history + re-assert, not a cross-structure copy.

---

## 5. Slices (executable order)

1. **`RETIRE` opcode** — add to `machine.py` (dataclass + `_apply` branch: delete rel's in/out fact edges
   and the rel node). Unit-test the opcode directly (deletes a fact edge that `DROP_CTRL` would refuse).
2. **Historical-record helper** — `record_history(graph, rel)`: assert the meta-visible historical record
   (+ retain the rel's provenance as reasoned-over data) IN the graph. No sidecar.
3. **Retraction driver rewrite** — `retract()`: cascade (unchanged) → record history → retire. Remove
   `INTERPOSE_RULE` from `RETRACT_RULES`.
4. **Resurrection** — `resurrect()` reads the in-graph historical record and re-asserts the fact.
5. **Privilege-gate test** — assert the rule→program lowering never emits `RETIRE` (e.g. no `Rule` can
   produce it; only the driver does).
6. **Behavior assertions** — after `retract`: the retracted fact no longer matches in ORDINARY reasoning
   (its live relation edges are GONE — no `<retracted>` splice); the historical record IS present and
   meta-matchable (the system can still answer "what did we believe / why retracted"); `resurrect` restores
   a matching fact.

---

## 6. Acceptance criteria

- **Existing retraction semantics preserved** (adapt `tests/test_retract_rules.py`): a retracted fact no
  longer matches (now because it's *deleted*, not spliced); the cascade removes the whole dependent chain
  below a retracted base; an `<axiom>` base fact is never cascade-retracted; no-retract is a no-op.
- **NEW — real deletion, no zombie:** the retracted fact's LIVE relation is gone (no `<retracted>` splice,
  no rerouted-but-present rel); `resurrect` restores a matching fact.
- **NEW — reflection preserved (the HARD CONSTRAINT):** the historical record + provenance remain
  **meta-matchable in the graph** — a meta-rule / `why` can still reason over what was believed and why it
  was retracted. (This is the acceptance test that guards against the sidecar mistake.)
- **NEW — privilege gate:** ordinary reasoning rules cannot emit `RETIRE` (structurally: not in lowering).
- **Full suite green** (346 baseline; `test_isa_interpose.py`/`test_rewire.py` still pass — the opcode is
  untouched, only unused by the TMS).
- **NOTE — perf is not an acceptance criterion here.** This probe does not claim to shrink the graph (history
  stays in it). Real shrink is a later GC policy; day-to-day cost is bounded by focus/attention.

---

## 7. Out of scope (do NOT expand into these)

- **Axis B (control registers)** — the second probe (§8). Not here.
- **General GC / forgetting** beyond retraction. The privileged-delete mechanism this probe adds is the
  foundation a later GC policy would reuse, but GC is not built here.
- **Multi-support re-derivation** — retraction is single-support today (over-retraction is recovered by
  monotone re-derivation, already noted in `retraction.py`). Unchanged.
- **A full capability/privilege system.** The gate here is "only policy drivers emit `RETIRE`." A richer
  capability model is a later concern if Axis A proves out.
- **Removing `INTERPOSE`/`RESTORE` opcodes.** Leave them; just stop using them in retraction. Their removal
  is a cleanup for after the probe succeeds.

---

## 8. The second axis (context only — NOT this probe)

For continuity, the other half of the thesis (from the same design conversation): **execution/control
state belongs in machine registers/pointers, not in data-graph nodes.** `State.regs` is already a register
file of pointers-to-nodes, used ephemerally and invisibly to rules; focus is conceptually a pointer but is
*implemented* as `<focus>` nodes. Lifting focus / iteration / call state into a **persistent control
register file** (control-flow ISA ops like `ITERATE` over a loop register, instead of MINT-ed control
nodes) would make the data graph pure facts and retire the `is_control` flag + `<…>` convention.

**Two HOMES, not three separate planes** (the corrected framing — ratified with the user):
- **the graph** holds everything *reasoned-over* — live **facts** AND their **explanation/history**
  (provenance, `why`, the retraction historical record). Explanation MUST be materialized as matchable data
  in the SAME graph, or the system cannot **reason about its own reasoning** (meta-rules, TMS, the retraction
  cascade). The data/explanation split is a **logical visibility scope** (ordinary reasoning sees current
  facts; meta-reasoning sees provenance/history — the existing inert/meta discipline), NOT a separate graph.
- **registers** hold execution state that explains nothing — loop counters, focus cursor, live demand agenda.
  This is the ONLY thing that physically leaves the graph.

The discriminating test:

> Does *anything reason about it* — including reasoning about the reasoning? If yes → **graph** (data or
> explanation, visibility-scoped). If it only answers *"how did the machine step?"* → **register**.
> `ITERATE`'s loop counter explains nothing → register; provenance is reasoned-over → stays in the graph.

So inspectability of `why`/`explain` is preserved by keeping explanation as graph data — moving *execution*
state to registers loses no explanatory power (a loop counter was never an explanation). Plus the earlier
**rule-visibility** criterion for what stays ordinary-visible vs meta-visible: *a rule must branch on it
(e.g. a `<check>` verdict) → it stays ordinary data; pure execution → register.* Captured here so it isn't
lost; it is a separate probe.

---

## 9. Files likely touched
- `ugm/machine.py` — `RETIRE` opcode (+ `_apply`).
- `ugm/retraction.py` — driver rewrite (cascade → record history → retire); remove `INTERPOSE_RULE` from
  `RETRACT_RULES`; add `record_history` / `resurrect` (all in-graph — no sidecar).
- `ugm/lowering.py` — confirm `RETIRE` is NOT emitted by any rule lowering (the gate).
- `tests/test_retract_rules.py` — adapt to deletion semantics; add resurrect / reflection / gate tests.
- `docs/implementation_plan.md` — log the outcome under the vision-cleanup residual.

## 10. Risks / judgment calls to flag back to the user
- Giving up "monotonicity is impossible to violate by construction" for "privileged-delete + gate." The
  probe must show the gate actually holds (reasoning can't delete).
- Cascade ordering: the cascade READS `proves`/`uses` to decide the set; retire DELETES the live relation.
  The driver must finish the **decide** phase before the **retire** phase (no interleaving), or the cascade
  loses its footing mid-run. (History-recording is additive/meta and safe at any point in the decide phase.)
- **Explanation-as-data is a HARD CONSTRAINT, not a preference** (§1): the historical record + provenance
  MUST stay meta-matchable in the graph so meta-reasoning survives. An earlier draft's "sidecar archive"
  was rejected for this reason — do not reintroduce it.
- Retraction becomes a *driver* (cascade rules + a privileged retire step) rather than pure same-graph rules,
  because the retire step is a privileged mechanism rules may not emit. That reframing is intended; worth
  confirming before going wide.

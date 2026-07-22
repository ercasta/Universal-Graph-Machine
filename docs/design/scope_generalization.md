# Scope Generalization — the one fundamental primitive on the critical path

> **Status: DESIGN (opened 2026-07-22).** Derived from `form_inventory.md` §9.1–9.3 (the binder
> spike). The spike found that of the two missing fundamental primitives, exactly ONE is on any
> agentic core's critical path: **relativizing a fact to a context, and letting rules bind that
> context** — i.e. generalizing SCOPE. It is an *extension* of the existing scope mechanism, and it
> converges three things that looked separate: the negative-band leak (§9.1), attribution (§4a), and
> tense-core (§9.2).

## 1. Why this is one primitive, not three

A band, a time index, and an attribution-holder are all the same shape: **the fact holds RELATIVE TO
something.** `has(lion,mane)` is true *to degree 0.75* / *at time t2* / *according to naturalist N*.
The substrate already has the relativizer — a SCOPE — so the three unbuilt-looking capabilities are
one extension of one mechanism.

## 2. The mechanism today (grounded, not assumed)

- A **scope** is a `<hypothesis>` node (`suppose.py`, `possibility.py`).
- A **scoped fact** is a CONTROL rel node carrying a `SCOPE` valued attr → the scope node
  (`suppose._pencil`). It is invisible to ordinary matching (control), visible only within its scope.
- The scope carries **relativizer data**: `<likeliness>` (a graded band). fork = scope **+** band;
  suppose = scope with no band. So "a scope carrying a relativizer" is ALREADY the pattern.
- The **read** is scope-aware: `check(..., scope=)` / `chain_sip(..., scope=)` reason within a scope;
  banded mode overlays the scope's pencils with a possibility discount (`_band_present`).
- **Provenance** relates facts in an inert layer (`J --proves--> C`, `J --uses--> P`) — explanation and
  retraction ride this, and it is what keeps a scoped derivation explainable (the ② constraint).

## 3. What is missing (from the spike, measured)

1. **Scopes are EPISTEMIC only.** The overlay treats a scoped fact as a POSSIBILITY (banded). An
   ontological scope (time, holder) means the fact holds DEFINITELY *in that context* — no discount.
   There is no scope KIND to dispatch the read on.
2. **The relativizer read is ASYMMETRIC.** `check`'s positive branch reads the band (`_band_present`);
   the ENTAILED_NEG branch reads crisp (`_present`) — the verified negative-band leak (§9.1). Its own
   docstring: "a graded hard-negative is out of slice."
3. **Scopes are not RULE-BINDABLE.** A rule reasons *within* one scope; there is no scope-variable, so
   cross-context inference (`fact in s1 ∧ s1 before s2 ⇒ fact in s2`, the frame axiom) is unwritable.

## 4. The design: a scope is a KINDED relativizer

Generalize the scope node to carry a **`kind`** and kind-specific relativizer data, and parameterize
the read by kind:

| kind | relativizer data | read semantics |
|---|---|---|
| `epistemic` (today) | `<likeliness>` band | possibility overlay, discounted |
| `holder` (attribution) | a holder id | facts hold DEFINITELY *for that holder*; global check is `assumed-no` (non-veridical) |
| `temporal` (tense) | an ordered index (+ `before`/`succ`) | facts hold DEFINITELY *at that index*; reasoning ranges across indices |

The `epistemic` row is exactly today's fork — so the generalization is additive. `holder` and
`temporal` are ONTOLOGICAL (no possibility discount): a fact in a holder/time scope is not "possibly"
true globally, it is definitely true *there*.

> **✅ REALIZED IN CODE 2026-07-22 (suite 900 green): the two ontological rows are ONE parameterized
> core.** `holder` and `temporal` were built as near-copy modules (`attribution.py`, `temporal.py`) to
> validate that kind dispatch generalizes with zero read-engine change — proven across both. They are
> now collapsed into `ugm/scope_kinds.py`: a kind-parameterized core (`scope_of` / `pen_scoped` /
> `holds_in` / `scopes_holding`) plus thin kind-bound verbs (`consider`/`holds_for`/…,
> `at_time`/`holds_at`/`order`/…). The ENTIRE axis of variation between the two kinds is a
> `(kind, key_attr)` pair plus two policy flags — `resolve_key` (temporal's index is an orderable
> entity) and `materialize` (temporal's read mints the queried scope for a cross-index rule to pen into).
> `test_scope_kinds.py` drives the core through a SYNTHETIC third kind with negative controls, proving
> the parameterization is real. The `epistemic` row stays in `suppose.py`/`possibility.py` (it carries a
> band, its read is discounted, and it is not entity-keyed — deliberately NOT folded in). The `@?t`
> rule-binding path in `chain.py` is still hardcoded `temporal` — ranging `@?t` over other kinds is the
> deferred "family-B" work.

## 5. Slices — each delivers a real capability and de-risks the next

**Slice 0 — SYMMETRIC relativizer read (the negative-band fix). START HERE.**
The smallest, independent, and it closes the verified leak. In `check`, when `policy.banded`, the
ENTAILED_NEG branch must read `_band_present` (not crisp `_present`) and return a banded-negative
verdict, symmetric with the positive. Stays entirely within the `epistemic` kind; introduces no new
kind and no rule-binding — but it establishes the invariant "a scope's relativizer is read on BOTH
polarities", which every later kind depends on. Site: `ugm/check.py` (the `elif`/neg block, lines
~114–135). Acceptance: `spike_epistemic_closure.py`'s `hedge∘negation` and `conditional∘negation`
turn from LEAK/decline to a banded verdict.

**Slice 1 — the `holder` kind (attribution). ✅ LANDED 2026-07-22 (suite 831 green).**
The mechanism (pencil scope) exists; this adds a KIND field, holder-keying, and a kind-parameterized
read where the overlay is ONTOLOGICAL (no discount) and a global check is non-veridical (`assumed-no`
for a penned proposition — §4a already notes `check` returns assumed-no for a penned proposition, so
this is close). NO ordering, NO cross-scope rules — so it validates kind dispatch cheaply, and it
delivers a §4a "mechanism exists, surface unbuilt" block. Acceptance: assert *N considers the lion a
cat*, and `is the lion a cat` answers no-globally / yes-relative-to-N.

> **As built.** The kind fork resolved to a **`kind` valued attr** (`suppose.SCOPE_KIND`, default-absent
> ⇒ `KIND_EPISTEMIC`), per the §6 recommendation. Probing FIRST showed the read was ALREADY ontological
> and non-veridical (a crisp `check(scope=holder)` sees the pencil ⇒ POSITIVE; a global `check` never
> sees a control pencil ⇒ ASSUMED_NO; a holder scope carries no `<likeliness>` so the banded overlay
> never discounts it) — so no read-engine change was needed. Slice 1 is the KIND + KEYING + AUTHORING
> layer only: `ugm/attribution.py` (`consider` / `holds_for` / `holder_scope_of` / `holders_considering`),
> a `<holder>` key giving one reused scope per party, `tests/test_attribution.py` (11, re-broken on both
> polarities of the invariant). The kind attr's live payoff is Slice 2's dispatch; here it labels,
> keys, and proves additivity (existing forks stay unkinded).

**Slice 2 — `temporal` (ontological ordered) scopes + rule-binding. ✅ COMPLETE 2026-07-22 (engine 848 green; CNL `@?t` surface 880 green).**
Two hard parts, in order: (a) an ontological ordered scope (a time index with `before`/`succ` — the
ordering itself is native relational content, spike O1); (b) SCOPE-VARIABLE rules — a rule that binds
a scope and relates two (`fact @?s1 ∧ ?s1 before ?s2 ⇒ fact @?s2`). (b) is the genuinely new
mechanism (§6 fork). This is tense's core.

> **Part (a) LANDED 2026-07-22 (suite 840 green).** `ugm/temporal.py` — a near-copy of attribution:
> `KIND_TEMPORAL`, keyed to an index entity by `<temporal-index>`; `at_time` / `holds_at` /
> `temporal_scope_of` / `order` / `indices_holding`; ordering is ordinary ink between the index
> entities. `tests/test_temporal.py` (9). Confirms kind dispatch generalizes past holder with no
> read-engine change.
>
> **Part (b) semantics PROVEN NATIVE (probe 2026-07-22) — the wall is ONLY the rule language.** The
> binary-fact frame axiom, hand-driven over the scope helpers (`indices_holding` → ink `before` →
> `at_time` at the later index), flips `holds_at(t2)` positive and stays non-veridical globally. So
> the O2b "4-place" wall is dissolved by the scope encoding (no reification, no 4th slot). What is
> left is expressing it AS A RULE — the §6 fork. The probe also settled the FORMULATION: because the
> scope is keyed to an ordinary index entity, the frame axiom ranges over the INDEX ENTITY, not the
> scope node (`has(x,y)@?t1 ∧ ?t1 before ?t2 ⇒ has(x,y)@?t2`, `?t` an ordinary variable), so the new
> mechanism is a per-atom RELATIVIZER `@?t`, not a scope-node binding.

## 6. Constraints and open forks

**Constraints (settled, not up for grabs):**
- **Explainability (the ② constraint).** A scoped/relativized derivation MUST go through
  `record_firing` with its scope intact, so `proves`/`uses` stays complete and `why` can explain a
  relativized conclusion. Provenance already relates facts; keep it complete for scoped firings.
- **No labeled edges / no Davidsonian reification** (`spo-directed-path-no-labeled-edges`). This is
  WHY time is a SCOPE, not a 4th S-P-O slot or an event node. The design must not reintroduce either.
- **Band lives on the scope** (S7.0), not the edge — the generalization keeps relativizer data on the
  scope for every kind.

**Open forks (to decide before the slice that needs them):**
- ~~**Scope-variable rule syntax + matching**~~ **SETTLED 2026-07-22 (Slice 2 part b, user decision): a
  per-atom RELATIVIZER `@?t` on the atom (`Pat.rel`), ranged over the INDEX ENTITY** (not the scope node
  — the probe's reframing, since the scope is keyed to an ordinary index). ENGINE BUILT on the demand
  path: a relativized body atom ranges temporal-scope pencils binding the index; a relativized head pens
  into the scope keyed to its bound index; the head's `?t` binds to the run-level scope's index at seed
  time (non-veridical globally). Additive — un-relativized atoms unchanged (848 green). ✅ The CNL surface
  (`@?t` in the machine-rule grammar) LANDED 2026-07-22 (880 green) — Slice 2 is complete. DEFERRED
  limits (not needed for acceptance): a relativized `not S P O @?t` clause and a relativized PROSE head.
- ~~**How `kind` is represented**~~ **SETTLED 2026-07-22 (Slice 1): a `kind` valued attr on the scope
  node** (`suppose.SCOPE_KIND`, default-absent ⇒ epistemic), not distinct marker names. Chosen because
  it is additive (joins the relativizer-attr family on `<hypothesis>`), gives uniform one-attr dispatch
  (`scope_kind`), and leaves all the scope machinery — which keys on the `SCOPE` tag + `<hypothesis>`-ness,
  never the marker name — untouched.
- **Scope-variable rule syntax + matching** — how a rule binds and relates scopes. This is the deep
  new mechanism and the real cost of Slice 2. *Deferred* — do not design it until Slice 1 validates
  kind dispatch; it may inform the syntax.

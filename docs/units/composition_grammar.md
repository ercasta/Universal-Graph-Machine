# A grammar over closed-class composition — sketch, pending review

**Status: design sketch, not yet implemented, 2026-07-28.** References `cnl_engine_goal_plan.md` (this is a
candidate approach to Phase C — proving composition sound — and to the `conditional`-detachment finding in
`closed_class_inventory.md` §5). Terms below marked *(proposed)* are not yet agreed — see `glossary.md`; don't
reuse them elsewhere until confirmed.

---

## 1. The problem this is answering

Up to now, composition safety has been checked *after* the fact: build a combination, run it, see if it leaks
(`sieve.py`), or ask a solver whether *any* combination violates a rule (`smt_sieve.py`). Both found real leaks
(`degree ∘ negation`; the `ask`/`language` leaks; `conditional`'s detachment leak, which guarding does not fix).

The idea here is different in kind: instead of allowing every combination and policing it afterward, define what
combinations are *constructible* in the first place, so the bad ones are never built rather than built-and-then-
rejected. Same family of move as a type system that makes illegal states unrepresentable, Zave's telecom
architecture (composing through fixed wiring paths, never shared state), and NetKAT (a small algebra with a
proven equational theory) — all discussed earlier in this thread.

**Not a token grammar.** An ordinary grammar's terminal is one fixed symbol; here, what sits at each position is
a *constraint* — a small set of allowed values for that slot (`polarity` is `pos` or `neg`; `force` is `assert`,
`ask`, or `command`) — and a claim is several such slots held **at once**, not a sequence. The closest existing
shapes: an **algebraic data type** (programming languages — a record of typed fields, with a recursive choice
between kinds of record) and a **feature structure** / **attribute-value grammar** (linguistics — HPSG, LFG;
used for exactly this reason, because natural-language combination isn't token-sequence-shaped either).

---

## 2. The bundle — *(proposed)* **BareClaim**

One value per **measured, independent slot** — not a fixed axis count. `closed_class_inventory.md` measured 9
independent slots for the current `CANDIDATES` set; the ones with real teeth (a `forbids`, or load-bearing for
an agentic scenario) are drawn on below. Any value of any field combines freely with any value of any other —
that's the orthogonality already argued for CONTENT/FORCE/LEVEL in `forms_discourse.md` §2.2, generalized to
however many slots actually get measured, not capped at three.

```
BareClaim:
    polarity:  pos | neg                          # slot: positive / negation / deny
    degree:    absent | present(band)              # slot: degree / hedge
    force:     assert | ask | command               # slot: assert / ask / command
    level:     world | language                     # slot: world / language
    modality:  absent | obligation | permission      # slot: norm / modality
    tense:     absent | past                          # slot: past — singleton; still an open hypothesis
                                                        # (closed_class_inventory.md §4), not yet confirmed
                                                        # independent by exclusion
    source:    absent | hearsay                        # slot: evidential — rescued by the audit-trail
                                                        # scenario (agentic_scenario_catalog.md §8)
```

**Deliberately excluded:** `mirative`. The scenario catalog found no agentic use for it (§7 of
`agentic_scenario_catalog.md` dissolved into `identity` + a new force instead) — excluded on purpose, not
forgotten.

---

## 3. The relational wrapper — *(proposed)* **RelationalClaim**

`conditional` doesn't add a field to the bundle — it relates two whole claims, which is why it needed its own
top-level shape rather than another slot:

```
RelationalClaim:
    when:  Claim        # the antecedent — a full claim, satisfied or not
    then:  Claim         # the consequent — a full claim
```

---

## 4. The top level, and where the real recursion is

```
Claim := BareClaim | RelationalClaim
```

A choice, not a merge — a bare claim and a conditional's `then` are never the same node. `RelationalClaim`'s
`when`/`then` are each a full `Claim`, so a `then` can itself be a `RelationalClaim` (nested conditionals). That
is genuine, unbounded recursion, and it is where the inductive argument from earlier in this thread is actually
needed — nothing here proves nesting terminates or stays safe at depth; that's a separate obligation, checked
against this shape rather than against free-form composition.

---

## 5. Checked against what's already been found

| finding | fixed by this shape? | how |
|---|---|---|
| `degree ∘ negation` leak | **no, not by itself** | this was one field's rule not consulting the *other* fields already in its own bundle. The bundle makes it explicit which fields are in scope to check (everything in `BareClaim`) but each field's rule still has to actually check them — that discipline doesn't come for free |
| `ask`/`language` leaks | same as above | same reason — a scoping aid, not an automatic fix |
| `conditional` detachment leak | **yes, structurally** | a `BareClaim` and a `RelationalClaim`'s `then` can never be the same node under `Claim := BareClaim \| RelationalClaim`. Saying both "unconditionally dangerous" and "conditionally more so when provoked" produces two separate `Claim`s, never one node fighting itself |

---

## 5a. The inductive step, checked — ⭐ nesting is safe only under one specific wiring discipline

`units/smt_sieve.py`'s `check_inductive_step()` states the two-part proof this grammar makes possible: **base
case** — a `BareClaim` alone is safe (already proven, §5's SMT check, `unsat` for `negation`/`ask`/`command`/
`language`); **inductive step** — *assuming* whatever sits inside a `RelationalClaim`'s `then` is already
known-safe, does wrapping one more conditional around it stay safe? Unlike sampling specific depths, an
inductive step proven once covers every depth at once — the same reason ordinary counting induction doesn't
need to check every number.

**Result: it depends entirely on how the outer conditional is wired to the inner one.**

| wiring | result | meaning |
|---|---|---|
| **naive** — outer fires on its own antecedent and concludes the final predicate directly, never checking whether `then` is itself a conditional | **`sat` — leaks**, even assuming the inner claim is already safe on its own | the same detachment bug resurfaces one level deeper; adopting the grammar does **not** make nesting safe automatically |
| **gated** — outer fires on its own antecedent, but concludes only whatever the inner claim itself concludes (which, by the induction hypothesis, already respects the inner antecedent) | **`unsat` — safe, at every depth** | the outer must never bypass the inner's own gating; it may only "unlock" it |

**This is now a concrete design requirement, not a hope — and, correcting an earlier conflation, it has nothing
to do with SUPPOSE's discharge (shelved, `cnl_engine_goal_plan.md` §3).** This is about *evaluating* an
already-authored nested rule ("if A, then: if B then C," given A and B) — modus ponens applied twice, purely
elimination-side, no hypothesis-introduction involved. Whatever mechanism handles nested conditional evaluation
must implement the "gated" wiring specifically — an outer conditional's firing must hand off to the inner
claim's own conclusion rather than asserting an answer itself. Get that right and nesting is provably safe at
unbounded depth; get it wrong (the "naive" shape) and the detachment leak returns at every level of nesting.
This is squarely still needed (`agentic_scenario_catalog.md` scenarios 1 and 6 both evaluate authored
conditional rules) and is not blocked by shelving discharge.

---

## 6. Left open, on purpose

- **`quantification`, `causation`** — future `RelationalClaim`-shaped siblings, each needing their own design
  the way `conditional` just got one. Structurally isolated from everything else once added, but not designed
  yet.
- **A new `flag`/`alert` force value** (from the drift-detection scenario, `agentic_scenario_catalog.md` §7) —
  cheap: one more value in the existing `force` field, not a new structure.
- **Termination/safety of nested `RelationalClaim`s at arbitrary depth** — not argued here, only made into a
  well-posed question by giving recursion an explicit shape to be inductive over.

---

## 7. Next step, if this shape is approved

Turn this into an actual Python structure in `units/`, and re-run the existing sieve/SMT checks against claims
built this way instead of the current flat "decorate one shared node" approach (`units/forms.py`), to see which
known leaks disappear by construction versus which still need each form's rule written correctly on top of it.
Not started — this document is the design to review first.

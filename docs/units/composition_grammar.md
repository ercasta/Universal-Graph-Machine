# A grammar over closed-class composition — sketch, pending review

**Status: design sketch, not yet implemented, 2026-07-28; §8 added 2026-07-29.** References `cnl_engine_goal_plan.md`
(this is a candidate approach to Phase C — proving composition sound — and to the `conditional`-detachment finding
in `closed_class_inventory.md` §5). Terms below marked *(proposed)* are not yet agreed — see `glossary.md`; don't
reuse them elsewhere until confirmed. **§8 supersedes an in-conversation sketch that never landed here** — and/or
were considered as free-standing siblings of `RelationalClaim`, each with an independent consequent; that shape
was wrong (see `computation_units.md` §3–4) and was corrected before being written down, not after.

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

- **`quantification`, `causation`** — ⚠ 2026-07-30: this framing is likely wrong for `causation` (already
  confirmed sugar, `causation-core-was-sugar`) and possibly for `quantification`'s open case (resolves via
  goal machinery, not a new closed-class design) — see `closed_class_rechallenged.md`. Neither may need "its
  own design" the way `conditional` did; both may be open content read by a generic meta-rule instead.
- **A new `flag`/`alert` force value** (from the drift-detection scenario, `agentic_scenario_catalog.md` §7) —
  cheap: one more value in the existing `force` field, not a new structure.
- **Termination/safety of nested `RelationalClaim`s at arbitrary depth** — not argued here, only made into a
  well-posed question by giving recursion an explicit shape to be inductive over.

---

## 7. Next step — ⭐ partially done, 2026-07-28

The detachment leak (§5's table) is now **fixed in running code**, not just designed: `Form.excludes_defaults`
(`units/forms.py`) stops `frame()`/`cells()` (`units/sieve.py`) from auto-attaching a bare `positive` onto
`unmet`'s node when nobody asked for it — the specific manufactured collision that was causing the leak.
`guard_density(CANDIDATES)["still_leaking"]` is now empty; the only leak `interactions()` still finds is the
explicitly-requested `positive ∘ unmet`, correctly. Full details and numbers: `closed_class_inventory.md` §5,
`cnl_engine_goal_plan.md` §5.

**This was a smaller, more surgical fix than the full `BareClaim | RelationalClaim` Python type this document
sketches** — it corrects the cell-*generation* discipline rather than restructuring `conditional` to use a
genuinely separate consequent node. What's still not built: a real, nested `Claim` structure in `units/` capable
of representing "if A, then: if B then C" as actual graph data (needed to test the §5a induction's "gated vs.
naive" finding against the real engine, rather than only against `smt_sieve.py`'s abstract model). That remains
open.

---

## 8. And/or — `Trigger`, a fan-in shape at the antecedent position, not a sibling of `RelationalClaim`

Worked out against a concrete example (`computation_units.md` §2: "if the circle is red or green, then: if
blinking fast: if red, press A, otherwise B") and against two corrections made getting there (same doc, §4). The
finding: `and`/`or` are never full `Claim`s carrying their own consequent. They only occur **inside** a
`RelationalClaim`'s antecedent, fanning into one shared `then`:

```
Claim    := BareClaim
          | RelationalClaim(when: Trigger, then: Claim)

Trigger  := BareClaim
          | All(Trigger, Trigger)      -- AND-fan-in: fires only once every branch has delivered
          | Any(Trigger, Trigger)      -- OR-fan-in: fires once any branch delivers; every branch of one
                                        --   `Any` is wired to the identical `then` — never to independently
                                        --   authored continuations
```

This is sound **by construction**, the same way §5's detachment fix is: a grammar that only ever gives one
`then` per `RelationalClaim` cannot represent two continuations that merely *happen* to agree, so nothing needs
checking that they do. `Any(A,B) → C` unfolds mechanically to `(A → C)` and `(B → C)`, because both wire to the
identical `C` — which is also why `if X then A else B` is conjunction-shaped (`X → A` plus `¬X → B`, `¬X` matched
directly via §4's θ mechanism), never disjunction-elimination, and needs nothing beyond ordinary gates.

**Deliberately excluded, same reasoning as §6:** a free-standing disjunctive `Claim` from which something new is
*derived* independently under each disjunct (rather than applied through a shared `then`). That is genuine
proof-by-cases and is exactly `SUPPOSE`'s discharge — shelved (`cnl_engine_goal_plan.md` §3) for lack of a
scenario that derives rather than applies. A bare disjunction asserted with nothing conditioned on it (*"the
circle is red or green"*, full stop) is harmless content, not an elimination problem — it only becomes one if
something tries to fan into two different continuations instead of one.

**No standalone `Negation` combinator either.** "If not X" is `Trigger` matched absent (§4's θ mechanism, already
in the engine), not a new node. Sentential negation of a whole combination doesn't arise in the
evaluate-an-already-authored-claim setting this grammar targets.

**Not built:** `All`/`Any` don't exist in `units/` yet — nothing to build against until this shape is reviewed
the way `conditional`'s was.

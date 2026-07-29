# Computation units, wires, and the one discharge point — worked examples

**Status: design note, 2026-07-29, consolidating a conversation that corrected two errors along the way (both
recorded below, not smoothed over).** Read `model.md` §5–§6 first; this document adds nothing to that model, it
walks a worked example through it and draws the grammar consequence for `composition_grammar.md`.

---

## 1. The two axes, kept separate

Two different questions get asked about any unit's output, and conflating them is where this thread went wrong
twice before landing:

- **Does it persist across a revive?** A **computation unit**'s output is an overlay — recomputed from its
  inputs every revive, gone the instant an input goes (`model.md` §5, "computation unit ... produces overlays").
  A **mutating rule**'s output is applied to the asserted layer at write-back and stays (`engine.py`:
  `write_back()`, "A computation unit's output is never applied; it is recomputed").
- **Can anything else match it?** There is no privileged partition hiding one kind of fact from another — "a
  machinery partition invisible to matching was considered and rejected" (`model.md` §6). Anything written to the
  graph is, in principle, matchable.

The safety property this document is about rests entirely on the **first** axis, not the second. Nothing needs
to be hidden from matching. What matters is that nothing is written *permanently* before it has earned that.

---

## 2. Worked example

> "If the circle is red or green, then: if the light is blinking fast: if the circle is red, press button A,
> otherwise button B."

### 2a. Built as a circuit

```
[match: red]  ──┐
                 ├──Any──▶ (unlocks) ──▶ [match: blinking fast] ──▶ (unlocks) ──▶ ┬─ [match: red]      ──▶ press A
[match: green]──┘                                                                 └─ [match: ¬red]     ──▶ press B
```

Every arrow is a wire; every box is a computation unit with input gates and one output. `match: red` and
`match: green` are two separate units, both wired into one `Any` unit — the fan-in. The `Any` unit's single
output feeds the *same* downstream unit regardless of which branch supplied it. Nothing downstream of the fan-in
knows or cares which disjunct fired; there is only one continuation, not two.

The final step — `press A` / `press B` — is the **only** place a fact is written to the world. Everything above
it is a computation unit passing a value along a wire. If it is realized as a **mutating rule**, pressing the
button is real and persists. If the light stops blinking fast the next revive, `press A`'s computation-unit
overlay simply is not re-derived — nothing needed to retract it, because nothing about the intermediate matches
was ever written anywhere permanent.

### 2b. Why this unfolds to two conjunctions

`Any(red, green) → continuation` is exactly `(red → continuation)` **and** `(green → continuation)`, because
both disjuncts are wired into the identical continuation node. There is no independent continuation per branch
to keep in sync, so there is nothing to prove they "agree" — agreement is guaranteed by the wiring, not checked
at runtime. That is why the sentence, unfolded, reads as "if blinking fast and red, press A; if blinking fast
and green, press B" with no trace of disjunction-elimination machinery anywhere in it.

### 2c. `if X then A else B` is not disjunction-elimination

The "otherwise" clause is `if red then A` plus `if ¬red then B` — two ordinary conditionals, one on a directly
matched antecedent, one on that antecedent's absence (`model.md` §4's θ mechanism: "nothing matched P above θ").
Nothing here assumes a branch and derives forward; each conditional's gate is filled, or it is not, and the unit
fires or does not. This is conjunction-shaped, not disjunction-shaped, and needs nothing beyond ordinary gates.

---

## 3. What this rules out of the grammar, and why

`composition_grammar.md`'s original sketch treated `Conjunction`/`Disjunction`/`Negation` as siblings of
`RelationalClaim` — full `Claim`s in their own right, each arm carrying an independent consequent. That shape
reopens exactly the problem it looks like it avoids: two independently-authored continuations that merely
*happen* to agree need something to check that they agree — the classical proof-by-cases discharge, run at
each branch as its own hypothesis, joined only if both sides converge. That is real machinery (an enumerator's
cursor over the hypothesis list, held by a mutating rule so it survives across revives — the only way anything
survives a revive at all — comparing results, concluding only on agreement), and it is exactly `SUPPOSE`'s
discharge, already shelved (`STATUS.md`) for lack of a scenario that derives rather than applies.

The corrected grammar (`composition_grammar.md` update pending) puts `All`/`Any` **inside** `Trigger`, at the
antecedent position of a `RelationalClaim`, always fanning into one shared `then`:

```
Claim    := BareClaim
          | RelationalClaim(when: Trigger, then: Claim)

Trigger  := BareClaim
          | All(Trigger, Trigger)
          | Any(Trigger, Trigger)
```

This is sound **by construction**, the same way `conditional`'s detachment fix was sound by construction: a
`BareClaim` and a `RelationalClaim`'s `then` can never be confused (§5 of `composition_grammar.md`), and now an
`Any`'s two branches can never be wired to two different continuations, because the grammar only ever gives one
`then` per `RelationalClaim`. Nothing is checked at runtime; nothing *can* be built the unsound way.

What is **not** in this grammar: a free-standing disjunctive claim from which something new is *derived*
independently under each disjunct. That is genuine case-analysis, and it is out of scope for the same reason
`SUPPOSE`'s discharge is — every scenario so far only *applies* an already-authored claim, never derives one.

---

## 4. Two corrections made getting here, on the record

**First error: "only the free endpoint is a fact in the world."** Not quite — nothing is structurally hidden;
`model.md` §6 explicitly rejected a matching-invisible partition. The corrected claim is narrower and is the one
that actually holds: intermediate values are transient (gone if their input goes) and, separately,
**`assemble()` only ever reads wiring topology out of the asserted layer** (`engine.py`: `assemble()` calls
`solve(self.asserted, _WIRE_PATTERN)`), never out of a computation unit's transient overlay. So no unit is ever
*dynamically wired* in response to an intermediate value's content — a value only reaches a gate because a wire
already, persistently, connects that source to that destination. That is what makes the circuit picture actually
closed: not invisibility, but "nothing gets newly wired by what a computation unit happens to be outputting right
now."

**Second error: modeling `SUPPOSE` as a read-time configuration filter, analogous to a TMS label.** The
mechanism is simpler than that: "assume red" is ordinary graph data (a `supposes`-named cell, `engine.py`), an
axiom like any other, delivered on wires to whatever is wired downstream of it. `world()` and `powering()` do
filter reads by which suppositions a conclusion rests on — that part was real — but the filtering is a
**read-time convenience for the outer query** ("what do I believe in the base world"), walked backward over the
actual wiring (`powering()`), not a separate visibility mechanism units consult while firing. A unit never checks
what configuration it's in; it only ever sees its gates.

---

## 5. `define` + `Identify`: progressive substitution, tested against the real engine

A different question than nesting: can the *engine itself* — not a new closed-class form — be used to
progressively substitute open-class content, the way solving a small system of equations does? `Identify`
(`engine.py`, one of the five effect types) already merges two nodes into one; a rule of the shape "if X is
defined this way, identify X with what it resolves to" needs nothing new to try this.

**Built and run** (`units/substitution_experiment.py`, against `units/engine.py` directly, not a mock —
promoted alongside `smt_sieve.py` as a real, re-runnable check: `python -m units.substitution_experiment`):
`customer_discount → holiday_rate → standard_rate → ten_percent (value=0.10)`, one rule
(`Merge("x","y")` on a `defined_as` pattern), tested three ways.

| test | result |
|---|---|
| chain built dependency-order, reverse, and shuffled | **all three converge to `value == 0.1`, in one revive** — confluent for this case, measured not assumed |
| circular definition (`a defined_as b`, `b defined_as a`) | merges cleanly, no surge — the termination machinery handles the degenerate case for free |
| a second rule consuming the resolved value | **failed at first** — not a soundness problem, the tunnel (§5's `model.md` invariant 3: a unit sees only its gates) applying exactly as documented. `Identify` merging two nodes doesn't make the merged facts ambiently visible to every other rule; the consuming rule has to be wired to **both** the substitution rule's output **and** the original axiom carrying the base fact. Once wired to both, it fired correctly |

**What this means:** the core idea works, cheaply, with nothing new built — `Identify` already is the
substitution primitive. The real cost isn't soundness, it's wiring effort: a deep or wide equation system needs
every consuming rule deliberately wired to every fact it depends on. That cost is exactly what §7's System 1
(associative retrieval, design not code) exists to absorb — the tunnel is a System 2 property; System 1 is
what's supposed to notice a chain is relevant and propose the wiring, rather than requiring it hand-authored.

**Scope note, not tested here:** pure substitution (`Identify`) stops short of actual computation — solving
"2x + 3 = 7" needs an arithmetic step that isn't identification at all. That's exactly the delegated-tool-call
shape already found for aggregation: the engine drives *which* substitutions apply and *when*, a tool does the
arithmetic, the result merges back in the same way.

---

## 6. Open

- `composition_grammar.md` still states the old `Conjunction`/`Disjunction`/`Negation`-as-siblings shape and
  needs updating to the `Trigger`-fan-in shape above.
- No `All`/`Any` exists yet in `units/` — nothing to build against until the grammar update lands.
- Full disjunction-elimination (derive, not apply) stays exactly where `SUPPOSE`'s discharge was left: shelved,
  revives only if a scenario needs an agent to derive a shared conclusion under an unresolved disjunction rather
  than apply an authored one.

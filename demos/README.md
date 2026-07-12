# UGM demos

Five runnable, self-contained walkthroughs of increasing complexity. Each demo is a
single `.cnl` file: an ordinary CNL corpus (facts + rules) with the questions and a
guided walkthrough written inline as comments. Nothing to install — the runner adds the
repo root to the path itself.

```bash
python demos/run.py                          # run all four, in order
python demos/run.py demos/01_basics.cnl      # run just one
```

| # | File | Teaches |
|---|------|---------|
| 1 | [`01_basics.cnl`](01_basics.cnl) | Facts, one rule, forward chaining, `who` / `why`. The smallest interesting program. |
| 2 | [`02_chains_and_recursion.cnl`](02_chains_and_recursion.cnl) | Rules feeding rules: chaining and self-feeding **recursion** (transitive closure), nested `why` proofs. |
| 3 | [`03_negation_and_worlds.cnl`](03_negation_and_worlds.cnl) | **Negation-as-failure**, and the **closed- vs open-world** reading of "no" (CWA default, OWA opt-in). |
| 4 | [`04_graded_and_defeasible.cnl`](04_graded_and_defeasible.cnl) | **Graded attributes** (`very` / `somewhat`, the α-cut) and **defeasible defaults** that fill the unsaid unless overridden. |
| 5 | [`05_card_trader_playground.cnl`](05_card_trader_playground.cnl) | **Playground.** A collectible-card trading agent that DECIDES what to buy/sell — market conditions, rarity tiers, named cards, all layered — with a big menu of knobs to turn. |

Start at demo 1 and read top to bottom — the comments explain what the engine does
(which reasoning mode runs, how the rule lowers to opcodes, what `why` is replaying).

## Try changing them

Every demo ends with a **NOW TRY CHANGING IT** section: two or three concrete edits
(add a fact, weaken a rule, flip a degree, defeat a default) with the outcome to expect.
Edit the `.cnl` file, re-run it, and check the change. That is the fastest way to build
intuition for how facts and rules interact.

## How the runner works

The demo file is a normal CNL corpus. Three kinds of `#` line are read by the runner and
ignored by the engine (they are comments):

```
#-- a heading              prints a section header
#? who gets mango          asked with ask_goal; the answer is printed under it
#? [open: served] is …     asked with those predicates opted into open-world (OWA)
```

Everything else is plain CNL or a plain `#` walkthrough comment. Each question is answered
against a freshly loaded copy of the corpus, so every `why …` is a clean from-scratch
derivation trace. See the header of [`run.py`](run.py) for details.

## Writing your own

The programmatic entry point is three calls (see the repo README "Usage"):

```python
import ugm as h
kb, rules = h.load_corpus(open("demos/01_basics.cnl").read())
print(h.ask_goal(kb, "who gets mango", rules))     # -> ['alice gets mango']
```

A few surface rules the demos lean on, worth knowing before you author your own CNL:

- **Base-fact verbs are a small built-in set** in `load_corpus`: the copula (`X is Y`,
  `X is a Y`), `X wants Y`, `X in Y`, and the graded/declaration forms (`X is gradable`,
  `X is very Y`, `X is closed world`, …). Brand-new relation words are recognised in rule
  **heads** (which mint them), not as free-standing base facts.
- **A rule head is always a triple** — `S P O` or the copula `S is O` (e.g.
  `?p is well_traveled`). A bare two-word head has no object to assert.
- **Questions**: `is S P O` / `is S O` (yes-no), `who P O` (wh), `why S P O` (proof). For a
  copula-state predicate, ask `why alice is admitted` (with the `is`).

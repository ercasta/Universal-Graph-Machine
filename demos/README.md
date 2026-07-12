# UGM demos

Six runnable, self-contained walkthroughs of increasing complexity. Demos 1-5 are each a
single `.cnl` file: an ordinary CNL corpus (facts + rules) with the questions and a
guided walkthrough written inline as comments. Demo 6 is a Python script — a live,
multi-turn SESSION doesn't fit the `.cnl` shape (see below). Nothing to install — both
runners add the repo root to the path themselves.

```bash
python demos/run.py                          # run demos 1-5, in order
python demos/run.py demos/01_basics.cnl      # run just one
python demos/06_session_conversation.py       # the session demo (its own runner)
```

| # | File | Teaches |
|---|------|---------|
| 1 | [`01_basics.cnl`](01_basics.cnl) | Facts, one rule, forward chaining, `who` / `why`. The smallest interesting program. |
| 2 | [`02_chains_and_recursion.cnl`](02_chains_and_recursion.cnl) | Rules feeding rules: chaining and self-feeding **recursion** (transitive closure), nested `why` proofs. |
| 3 | [`03_negation_and_worlds.cnl`](03_negation_and_worlds.cnl) | **Negation-as-failure**, and the **closed- vs open-world** reading of "no" (CWA default, OWA opt-in). |
| 4 | [`04_graded_and_defeasible.cnl`](04_graded_and_defeasible.cnl) | **Graded attributes** (`very` / `somewhat`, the α-cut) and **defeasible defaults** that fill the unsaid unless overridden. |
| 5 | [`05_card_trader_playground.cnl`](05_card_trader_playground.cnl) | **Playground.** A collectible-card trading agent that DECIDES what to buy/sell — market conditions, rarity tiers, named cards, all layered — with a big menu of knobs to turn. |
| 6 | [`06_session_conversation.py`](06_session_conversation.py) | **Session.** One live KB across many turns via `ingest`: facts, questions, mid-conversation rule authoring, `forget that rule` (disable), and `focus on` / `forget that`. |

Start at demo 1 and read top to bottom — the comments explain what the engine does
(which reasoning mode runs, how the rule lowers to opcodes, what `why` is replaying).
Demo 6 is a different layer (`ugm.ingest`, the multi-turn driver over the same CNL
surface) and reads on its own, after 1-5.

## Try changing them

Every demo ends with a **NOW TRY CHANGING IT** section: two or three concrete edits
(add a fact, weaken a rule, flip a degree, defeat a default) with the outcome to expect.
Edit the `.cnl` file, re-run it, and check the change. That is the fastest way to build
intuition for how facts and rules interact.

## How the runner works

A question in a demo file is a BARE line — no special marker. `is alice gets mango` is
recognized as a question (not a fact) purely by word order: `is` leads. `run.py` decides
this the same way `ingest` does, by asking `h.recognize(line)` whether a CNL question form
fires — never a runner-side keyword check. Facts read the other way round (`alice is a
customer`, subject first) and never match, so there is no ambiguity.

Two things in a demo file are NOT CNL, and stay marked:

```
#-- a heading              prints a section header (presentation only)
[open: served] is …        the question that follows, with `served` opted into OPEN-world
```

`[open: ...]` is a runner directive, not CNL: which predicates are open-world is a caller-side
POLICY (`FirmwarePolicy`), not domain content, so — unlike the question itself — it can't be made
"native" any more than a command-line flag could (`docs/architecture.md` §6).

Everything else is plain CNL (a fact/rule line `recognize` does NOT fire on) or a plain `#`
walkthrough comment. Each recognized question is answered against a freshly loaded copy of the
corpus via `ingest`, so every `why …` is a clean from-scratch derivation trace. See the header of
[`run.py`](run.py) for details.

## Writing your own

The programmatic entry point is three calls (see the repo README "Usage"):

```python
import ugm as h
kb, rules = h.load_corpus(open("demos/01_basics.cnl").read())
print(h.ingest(kb, rules, "who gets mango").answer)   # -> ['alice gets mango']
```

(`h.ask_goal(kb, "who gets mango", rules)` still works directly if you don't need the
fact/rule/focus routing `ingest` adds — see demo 6.)

A few surface rules the demos lean on, worth knowing before you author your own CNL:

- **Base-fact verbs are a small built-in set** in `load_corpus`: the copula (`X is Y`,
  `X is a Y`), `X wants Y`, `X in Y`, and the graded/declaration forms (`X is gradable`,
  `X is very Y`, `X is closed world`, …). Brand-new relation words are recognised in rule
  **heads** (which mint them), not as free-standing base facts.
- **A rule head is always a triple** — `S P O` or the copula `S is O` (e.g.
  `?p is well_traveled`). A bare two-word head has no object to assert.
- **Questions**: `is S P O` / `is S O` (yes-no), `who P O` (wh), `why S P O` (proof). For a
  copula-state predicate, ask `why alice is admitted` (with the `is`).

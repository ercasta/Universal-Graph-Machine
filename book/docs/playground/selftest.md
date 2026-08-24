# Make it check itself — live

Everything this book claims about the engine is checked by a suite that ships
*inside* the engine. Press the button and it runs here, on your device, in
front of you.

Each line is one check. A check fails if any of its named observations is
exactly `False`, and the tally at the bottom counts them.

<div class="ugm-playground"
     data-wheel="../wheels/universal_graph_machine-0.4.0-py3-none-any.whl"
     data-mode="selftest">

  <div class="ugm-controls">
    <button class="ugm-run" type="button">Run the self-test</button>
  </div>

  <div class="ugm-steps"></div>
</div>

!!! note "It takes a moment"
    179 checks, each building a small world and reasoning over it, inside a
    Python runtime that is itself running in your browser. Give it a few
    seconds.

## What you're looking at

The checks are grouped by the section of the design document they belong to,
so scrolling the output is roughly scrolling this book. A few worth hunting
for:

- **`§14`** — matching and arbitration: how a rule's antecedent is tested
  against current belief, and how the table picks which applicable rule goes
  next.
- **`§16`** — applying a rule: what asserting and erasing actually do to the
  graph, and what *quiescent* means now that belief is presence rather than a
  history.
- **`§17`** — the web: the same reserved-vocabulary check behind Chapter 33,
  run here as part of the suite rather than as a standalone report.
- **`§19`** — triggers: a rule seeing what another rule is about to conclude,
  and adding beside it, replacing it, or dropping it — the whole of how norms
  and approval-gating are built.
- **`§20`** — attention: the queue, frames (the attention stack), and lanes
  (a second pass per round that isn't the default one) — engine state rather
  than a belief.
- **`§21`** — tools: a request answered by a function, landing a tick later,
  never concluding on its own.
- **`§22`** — the surface: what the grammar refuses outright, and the message
  it gives you when it does.

## Reading a failing check

Each check prints its own named observations rather than a bare pass/fail, on
purpose: a check that only says *FAIL* tells you something is wrong and
nothing about what. This suite was written to fail loudly rather than to
look thorough while testing nothing — Chapter 32 is about designing checks
so they can't lie, and the rule that guards it:

> **An agreement gate that agrees is worth nothing until it could have
> disagreed.**

A test suite that reads like a list of features tells you what someone
intended. One that reads like a list of near-misses tells you what actually
went wrong.

## The other instrument

The suite is the main one. There's also:

| | what it holds |
|---|---|
| `python -m ugm.gates.vocabulary` | every reserved name classified exactly once, against corpora that ship and actually run — Chapter 33 |

`docs/feature-requests.md` and Chapter 34 have the honest accounting of
what's still open beyond these two instruments.

---

[Back to running a corpus →](corpus.md)

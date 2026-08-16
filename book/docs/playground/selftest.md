# Make it check itself — live

Everything this book claims about the engine is checked by a suite that ships
*inside* the engine. Press the button and it runs here, on your device, in front
of you.

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
    Five hundred-odd checks, each building a small world and reasoning over it,
    inside a Python runtime that is itself running in your browser. Give it a few
    seconds.

## What you're looking at

The checks are grouped by the section of the design document they belong to, so
scrolling the output is roughly scrolling this book. A few worth hunting for:

- **`§6`** — the bootstrap. That the read is made of rules, and that a rule whose
  antecedent is entirely structural concludes structure.
- **`§8`** — the worked rules from the design, including the one whose
  `implies`/`causes` choice is what makes *a plan to cause rain by causing
  clouds* unwritable.
- **`§9`** — the signs, including the one that catches a `−` member matching *no
  entry* instead of a denial.
- **`§12`** — a hedged conclusion crossing into a supposition and coming back out
  wrapped. Weakest link as structure rather than as arithmetic.
- **`§13`** — a rule whose consequent is a bare variable believing what a channel
  said, **and** that the channel in the rule is the channel it was delivered on.
- **`R5`** — that the trail reaches the utterance. Not "some external source" —
  the actual arrival.

## Why some of the names shout

You'll see observation keys in capitals: `AND_INVENTS_NO_DERIVATION`,
`ASKING_CHANGED_NOTHING`, `BUT_IT_IS_NEVER_PROPOSED`.

Those are the **load-bearing** ones — the assertions that would still pass if
the feature were broken in the *obvious* way, so they were written to fail
instead.

Several exist because an earlier version of the same check passed without
testing anything. Chapter 32 has the list of instruments that lied here, and the
rule that came out of it:

> **An agreement gate that agrees is worth nothing until it could have
> disagreed.**

A test suite that reads like a list of features tells you what someone intended.
One that reads like a list of near-misses tells you what actually went wrong.

## The other instruments

The suite is one of several runners, and the others are gates rather than tests
— each holds a fast path to a slow definition, on every look, in every fixture:

| | what it holds |
|---|---|
| `python -m ugm.agreement` | the kept resolution against the raw walk |
| `python -m ugm.state` | the maintained state and its indices against the walk |
| `python -m ugm.arbitration` | the fast chooser against the slow one |
| `python -m ugm.quiescence` | the compiled verdict against the six rules that define it |
| `python -m ugm.bundle` | deletes each shipped rule and re-runs the suite |
| `python -m ugm.vocabulary` | unwebbed names, with a planted typo as a control |
| `python -m ugm.atlas` | the web: islands, bridges, dead rules, and pairs that could disagree |

And a set of **comparisons** rather than gates — each runs two loops, or two
runs, over the same corpora and reports where they differ:

| | what it compares |
|---|---|
| `python -m ugm.attention` | the table loop against the shipped one, in ticks and conclusions |
| `python -m ugm.teaching` | a table calibrated from one demonstration against an uncalibrated one |
| `python -m ugm.learning` | the same world run twice, with the second run allowed to be no better |
| `python -m ugm.practice` | rehearsing a goal inside a supposition against enacting it for real |
| `python -m ugm.table` | several agents talking, in-process against one OS process each |

They aren't run here because several of them take longer than a browser tab
deserves. From a checkout, they're one command each.

---

[Back to running a corpus →](corpus.md)

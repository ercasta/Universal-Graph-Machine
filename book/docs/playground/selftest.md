# Make it check itself — live

Everything this book claims about the engine is checked by a suite that ships
*inside* the engine. Press the button and it runs here, on your device, in front
of you.

Each line is one check, followed by the individual things it asserted. A check
fails if any of its keys is exactly `False`, and the tally at the bottom counts
them.

<div class="ugm-playground"
     data-wheel="../wheels/universal_graph_machine-0.2.0-py3-none-any.whl"
     data-mode="selftest">

  <div class="ugm-controls">
    <button class="ugm-run" type="button">Run the self-test</button>
  </div>

  <div class="ugm-steps"></div>
</div>

!!! note "It takes a moment"
    A hundred and forty-odd checks, each building a small world and searching
    it, inside a Python runtime that is itself running in your browser. Give it
    a few seconds.

## What you're looking at

Scroll the output and you'll find the claims from this book, stated as
assertions. A few worth hunting for:

- **`a_derivation_may_never_act`** — the purity bar from Chapter 23. Its last
  key plants the removal of the bar and confirms the question *dies* rather than
  quietly reaching outside.
- **`why_answers_from_history_and_never_invents_it`** — Chapter 8's refusal.
  `AND_INVENTS_NO_DERIVATION` is the key that matters.
- **`the_trace_is_an_observer_not_a_participant`** — the guarantee that the
  animation on the other playground pages is the real search.
- **`workbench_copies_are_structurally_unreachable`** — Chapter 6: the machine's
  imaginings can't be mistaken for the world.
- **`one_grammar_three_verbs`** — Chapter 9: `goal` and `ask` produce the *same*
  constraints.
- **`a_guideline_reorders_and_can_never_exclude`** — Chapter 17, and the two keys
  that carry it sit next to each other: forbidding a move makes the puzzle
  unreachable, *avoiding* the same move still solves it.
- **`a_procedure_refuses_where_a_method_falls_back`** — Chapter 18. Two
  decompositions built identically apart from one declared word, required to
  behave oppositely.
- **`ignorance_is_representable_and_sensing_closes_it`** — Chapter 19: *not
  there* versus *not looked*, end to end.

## Why the keys are named like that

You'll notice keys shouting in capitals: `ASKING_CHANGED_NOTHING`,
`BUT_IT_IS_NEVER_PROPOSED`, `SAME_CONSTRAINTS_FROM_BOTH`.

Those are the **load-bearing** assertions — the ones that would still pass if the
feature were broken in the *obvious* way, so they were written to fail instead.
Several of them exist because an earlier version of the same check passed
without testing anything, and the fix was to find the arrangement under which it
bites.

A test suite that reads like a list of features tells you what someone intended.
One that reads like a list of near-misses tells you what actually went wrong.

---

Back to [the planner →](tower.md) · [asking →](asking.md)

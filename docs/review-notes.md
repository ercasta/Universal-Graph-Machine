# Review Notes

Attention.py:
- check if _forgo and rivals can be removed.
- ⚠ Anchored at the SEAT rather than at every moment, which is the containment story as well as the cheap -> is this still true?
- "Satisfaction, ported from the tick this loop replaces" -> can't we leverage our "compute delta" to evaluate "satisfaction"? This would mean ALWAYS setting a "goal" and checking vs that.
- Is the following code section used? Moreover the second if repeats the "widened" instead of "recover"
```
if not window:
            # Nothing in the table matched. These are NOT ported logic.
            # →
            # docs/design/attention.md#nothing-in-the-table-matched-the-engine-says-so
            if m._widen():
                steps.append(Step(arrivals, 0, tried, None, (), "widened"))
                continue
            if m._recover():
                steps.append(Step(arrivals, 0, tried, None, (), "widened"))
                continue
            if m._wake():
                steps.append(Step(arrivals, 0, tried, None, (), "quiet"))
                continue
```

Chain.py has lots of boring stuff related to provenance, support, licence, etc. Probably overengineered.

Channels.py: probably we should demote channels to more "open world". An channels arrivals should get attentioned, using the standard mechanism

Gate.py talks about vetoes, review


sexpr.py probably to be deleted.


# New Features required:
- available to agent:
    - compute delta : computes the delta between two subgraphs (useful to get delta between desired and current state and make informed choices). Takes three nodes as param. Materializes 
    - install / remove pre-application or post-application "triggers" (they can query the delta and perform actions such as changing it). Stored in graph, but managed by engine. The agent could use this to "always remember" a prohibition or a directive.
- safety triggers (queries on rules - managed by the engine - e.g. to block "sensitive" actions, tool calls)

- fuzzy queries: define a concept like "old man" as a function of age rather than a
  binary predicate. Materializing the value is probably already possible with arithmetic
  on the RHS (computators already do arithmetic as a condition on the binding, so the
  degree can be computed and written). The point is not materializing it — it is using
  the degree to **weight the score on the LHS of a query**, so a rule about old men is
  more strongly applicable for an 80-year-old than a 60-year-old without either being
  excluded.

  The risk, and it is the whole of the design question: this conflates **partially true**
  with **partially relevant**, and they are not the same thing. "He is somewhat old" is a
  claim about the world that can be right or wrong. "This rule is somewhat worth applying
  here" is a claim about the agent's own search. A single number that does both cannot be
  argued with, because a disagreement about it has two possible subjects.

  Prior art in the repo to reconcile against before designing:
  - `weaker` was carried, composed, printed and never obeyed, then deleted: *there are no
    grades*. Uncertainty is `likely(p)`, a wrapper, so it is a proposition that can be
    denied. A degree of truth must not reintroduce a grade field.
  - the recorded ML seam is *the* PAIR — score (how good) beside grade (how sure) — which
    is the same split under a different pair of names, and is evidence the split is real.
  - `_attended_first` already sums per-node weights to order applications. That is the
    existing home for *partially relevant*, and it is ordering rather than confidence by
    construction. §9.5 (per-term weights on competence rules) is the parked item next to it.
  So the likely shape is: degree-of-truth is a claim in the corpus, degree-of-relevance is
  a weight the chooser reads, and the corpus writes the rule that turns one into the other.
  What must not happen is one number entering both.

- **`_` as a wildcard member argument.** `no subgoal(_, $w)` — *this slot, I am not picking
  anything out of.* It is the third route to deleting `_root` (the others being `_count`,
  which works today, and `_root` itself), and the only one that is a single member with no
  request round-trip. It is not a quantifier, which is why it is admissible where a free
  variable in a `no` member is not: a hole cannot bind, cannot be substituted, cannot appear
  in a consequent, and cannot reach the occurs-check hazard `_SAFE` guards.

  Rejected alternative, recorded so it is not re-proposed: **a variable used nowhere else**
  (Prolog's singleton rule) adds no notation, and should still be refused, because singleton
  inference makes a member's meaning depend on the rest of the rule. Add a member elsewhere
  mentioning that variable and the first member silently changes question, with no local edit
  and no error. That is the same non-locality that made free-variable `no` inadmissible.

  Rows, not branches: the `ABSENT` branch already grounds the pattern and asks
  `chain.resolve`; the wildcard case asks `Graph._by_arg` instead. That index already covers
  **structures**, which is what a goal is — measured: `instances_with(SUBGOAL, 1, ·)` gives
  `[]` for `boiling(kettle)` and one hit for `water(kettle)`. One lookup, where `_root` scans
  every `instances_of(SUBGOAL)` and filters. (The atoms-only index is `Situation`'s, over
  entries — a different index.)

  Trap that must be closed with it: **`no subgoal(_, $w)` loads today and is silently
  wrong.** `_` lexes as a name, so the member asks about a ground proposition nothing ever
  wrote — trivially absent, concluding rootedness for every goal including ones with a
  parent. `_` must stop being a plain name in argument position, or the obvious spelling
  stays a trap. Names *containing* `_` (`delta_next`, `at_or_after`) are unaffected: the rule
  is only about a name token that is exactly `_`. Note `Situation.ANY` is already the string
  `"*"` — different layer, no collision, but the word is spoken for.

- **Prefix binding syntax, `$x = goal(something)`.** Worth deciding, but note first that the
  capability already exists, postfix, and is verified working:

      rule <r> = implies( { +goal($w) as $x }, { +saw($x) } )
      saw(goal(boiling(kettle)))  +

  So this is a respelling, not a new feature, and it should be judged as one. Three things
  against changing it, none decisive on its own:

  - `as` is a **family**, not a one-off. `at $m` binds where an entry sits; `as $t` binds
    what matched. Moving one to prefix splits the family unless both move.
  - The same binder carries **computators**: `minus($x, $c) as $new`. Written
    `$new = minus($x, $c)` it reads as assignment, and the design is explicit that a
    computator *claims nothing* — it is a condition on the binding, not a computation whose
    result is stored. Prefix `=` would actively mislead exactly where the distinction is
    load-bearing.
  - Postfix puts the **pattern first**, which is the order the matcher works in and the order
    the member is read in.

  For it: `$x = ...` is the familiar reading order, and it puts the name where a reader
  scanning for *where is `$x` bound* will look. If it is adopted it should be adopted for
  `at` too, and the computator case should be spelled out in the same commit.

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


~~sexpr.py probably to be deleted.~~ **Deleted 08-22.** 335 lines and two entry points
(`syntax: lisp` on the first line, `lisp:` on one statement), referenced by nothing --
not the suite, not a gate, not a probe, not the book -- so no measurement covered it.
Suite green after removal with no check rewritten.


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


# Discussion

Let's think about it for a moment. 

We have been discussing about a world MODEL. A world model allows us to make hypotheses, or forecasts, or e.g find possible causes for a phenomenon, create expectations. it's different from the real world. Imagine the hanoi tower scenario. If i know the world model, i can play it in my head, play "with a friend" by just talking about an imaginary hanoi tower, or if i have one physical hanoi tower, i can play it in with my hands. There are two points i want to discuss. The first is the concept of "forbidden", "invalid", "refused", because they are probably something different from how we represented it. We represented it as something simply "undoble". The reality is more nuanced. 
If I am playing in my head, maybe trying to solve the hanoi tower, i can IMAGINE doing an invalid move, and CONCLUDE it would be invalid.
Nothing bad; I can "revert" my move mentally, and play another one. Now imagine I am playing with a friend. This might mean many things. It might be we are playing a game of mentally solving a hanoi tower. In this case, if i DECLARE the move to my friend, my friend can answer back it's an invalid move, and I lose the game with my friend. And if i play with my hands, nothing bad happens. The toy hanoi tower does not explode; if I am alone at home, i can even perform invalid moves, and nothing happens. If I am playing at an official hanoi tower tournament, i might lose the match, or get disqualified, whatever.
The implication for us: even if we are alway talking about the Hanoi Tower, what REALLY happens depends on the context: the three situations are very different. What stays constant is that we can REASON ABOUT THE FUNDAMENTALS of the Hanoi Tower in the same way, and I can probably STATE the move "I move A on B" in exactly the same way no matter whether we are playing in the head ("planning?"), or with a friend, or in a real tournament. so there is a CORE "world model" of the hanoi tower; but then we need an "outer" model, that keys not only on the move, but on the context. And also, this is a model too; so I could REASON about what would happen if i made an illegal move in a tournament; or I, as an agent, could actually MAKE the move, and incur real consequences. I.e. I need a MODEL of the tournament, or a model of PLAYING with a friend.
What I am saying is that the ENGINE should have no "hardcoded" handling or forbidden, invalid, refused. It's all in the models. The interesting thing is: HOW DO THEY COMPOSE? HOW do i create a "playing imaginary games with a friend" model that is able to handle all games, no matter of the rules? My hypothesis is that there are "bridge" concepts. The "tower of hanoi" model, if handed an "invalid" move, should simply state "this is an invalid move", and do nothing. 
Now also imagine we play "explosive hanoi tower", a physical version of the game, where an invalid move makes the toy literally explode. I could still leverage the "core" hanoi tower model, but i'd have to reason about the consequences more carefully.
What do you think?  

- ~~expert inheritance (`extends`)~~ **Deleted 08-22.** Measured in `docs/models.md` 12: an
  expert that absorbs another's rules wins the questions it borrowed, and duplicating a
  discriminating term raises its document frequency so it loses weight for every expert,
  including ones that inherited nothing. Sharing a rule everybody holds stays free (idf
  zero), which is why writing `fact +knows(X, <replied>)` out cost nothing. The old spelling
  now fails at load with a message naming the replacement.

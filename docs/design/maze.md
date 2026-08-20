# `maze.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

How far does a lesson transfer? A number per region -- and the theory
predicts the VARIANCE, not the mean.

    python -m ugm.learning.maze

`ugm.lifting` shows that a lesson generalises: `contains(_, :solid)` covers `k5`,
which holds pebbles and was never heated. That is one held-out case and one bit
of information -- covered or not -- and one bit cannot tell a good learner from a
lucky one. This asks the same question of a whole maze, and the answer is a
number per region.

## Why the mean is the wrong statistic, and it is not a subtlety

Three learners, scored by average coverage over the held-out regions:

  * **the memoriser** (no world model) learns `contains(_, sand)` and
    `contains(_, gravel)`, which have nothing in common, so there is no lesson
    at all and nothing transfers anywhere. Mean coverage **0.00**.
  * **the lifted learner** learns `contains(_, :solid)`. It covers the region
    that holds solids, misses the region that holds liquids, and half-covers the
    mixed one. Mean coverage **0.50**.
  * **an over-general learner** -- one that proposed `contains(_, :stuff)`, a
    kind everything has -- covers every case in every region. Mean coverage
    **1.00**.

> **Ranked by mean transfer, the worst learner wins.** A lesson that covers
> everything explains nothing, and *how much does it transfer* cannot tell that
> apart from a lesson that is right.

Ranked by **variance** across regions, the two failures collapse together and the
real learner separates: the memoriser transfers nothing everywhere and the
over-general learner transfers everything everywhere, and **both are flat**. Only
a lesson that is about a kind can cover one region and not another, so
**discriminating between regions is the observable, and a single number summed
over them destroys it.**

That is the whole claim, and it is why this is a separate instrument from
`ugm.lifting` rather than another check inside it.

## Holding out TERMS, not only relations

Every term the held-out regions contain -- `pebbles`, `grit`, `juice`, `chalk`
and the rest -- appears **nowhere in the training corpus**. That is checked
rather than asserted, because it is the one property the whole measurement rests
on: a fixture that held out only the *relation* while reusing the training terms
would let the memoriser recognise `contains(_, sand)` in a new room and score as
a generalising learner. What is held out is what the rooms are FULL OF.

⚠ The regions are authored (`in_region`), not derived from the doors. Connected
components would need a transitive closure, which is a corpus rule and not the
thing being measured -- and reading the region off `features` means a case's
region and a case's lesson are read by the same function, which is `features`'s
own reason for being at module level.

## What this does not do

**It does not learn in the maze.** The walker apparatus is `ugm.walkers`; a room
here is a place a case sits, and nothing traverses. What the maze contributes is
that the held-out cases are genuinely ELSEWHERE -- grouped, and grouped by
something other than the answer.

**And three regions is three numbers.** The variance is a direction, not a
statistic anybody should quote.

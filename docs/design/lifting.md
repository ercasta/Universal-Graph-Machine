# `lifting.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Does a lesson survive a second example? Only through the world model.

    python -m ugm.learning.lifting

`ugm.surprise` learns from one failed prediction by contrasting it with a
success: heating boiled the water and not the sand, so *sand* is what
distinguishes them. That works, and it does not transfer.

## The measurement that motivates this

Two kettles fail — one of sand, one of gravel — and the raw contrast gives two
different answers with nothing in common:

    lift=False   boiling(k2)  ['contains(_, sand)']
                 boiling(k3)  ['contains(_, gravel)']
                 COMMON  ->   []

So an agent learning this way memorises a value, then another value, for ever.
Every failure is its own case and nothing is ever concluded about a kind.

With the world model consulted — `is_a(sand, solid)`, `is_a(gravel, solid)` —
each feature is offered abstracted as well as raw, and the two failures share
one thing:

    lift=True    boiling(k2)  ['contains(_, :solid)', 'contains(_, sand)']
                 boiling(k3)  ['contains(_, :solid)', 'contains(_, gravel)']
                 COMMON  ->   ['contains(_, :solid)']

> **The ontology is not decoration. It is the difference between a lesson about
> a thing and a lesson about a kind**, and therefore between memorising and
> generalising.

## Transfer, measured on a case the learner never saw

`k5` holds pebbles. It is never heated, so it is neither a success nor a
failure and contributed nothing. The lesson covers it anyway, because pebbles
are a solid — and does not cover `k6`, which holds juice.

That is the whole claim of generalisation, and it is one lookup: does the
learned feature hold of a case that was not in the evidence?

## What decides it is the world model, not this code

The kill-probe is the check that matters. Delete one `is_a` fact — gravel stops
being a solid — and the common lesson collapses to nothing, while everything
else is unchanged. The generalisation is being done by what the corpus knows,
not by the learner being clever, and a learner that still generalised without
the ontology would be inventing the kind.

## What this does not do

**It does not promote the lesson.** The output is still a candidate. Whether
`contains(_, :solid)` should become a premise of `<boils>` is an authoring act,
and nothing here performs it.

**And one kind is not a taxonomy.** The lift is one level and one argument at a
time. A corpus rule making `is_a` transitive widens it with no change here,
which is the right place for that decision — but nothing here has measured what
a deep taxonomy costs.

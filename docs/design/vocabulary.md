# `vocabulary.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

What the engine reserves, and what a corpus has to borrow. (§10, §17, §22)

The user's observation, and this module exists to test it rather than agree
with it:

> Working with an open class beats traditional programming because you do not
> have to *implement* the meaning of everything. `owning` something, `selling`
> something -- you can create valid propositions and only give them a specific
> meaning later.

That is a claim with two halves, and both are measurable.

**How much does a corpus borrow?** Counted below per corpus: distinct relation
names written, against how many of them the engine already knew.

**What is the reserved vocabulary FOR?** The interesting half. If those names
were a domain -- a little ontology of times and things and actions -- then a
corpus would be writing *inside* someone else's world model, and the observation
would be much weaker than it sounds. The classification below says they are not:
the engine's vocabulary is about **the chain, the surface, rules-as-data, the
agent's own deliberation, and the seam where a world reaches it.** Not one of
them is about any world.

⚠ **The classification is a CLAIM, not a measurement**, which is why it is
written out name by name where it can be disagreed with, and why the partition
is checked for being total: a name nobody classified would otherwise vanish from
the count and flatter whichever bucket it belonged in.

## §4-§11: the history, and how to walk it.

§4-§11: the history, and how to walk it.
`licensed_by` sits beside `rests_on` and is here for its reason: *what
produced this entry* is a fact about the chain's own construction, not
about any world. ⚠ It arrived unclassified and this census is what caught
it -- see docs/observations.md §2.14, where the invariant was written down
one message before it fired.
`moved` sits here for `asking`'s reason rather than under deliberation:
both are about WHICH SEAT, which is a fact about the agent's place in the
history and not about what it is trying to do there.
`holds_at` and `time` are computed, not stored -- like `pred` and
`entry_of` beside them. Both were reserved in `core/chain.py` and never
classified here, which is the gap this gate exists to catch.

## `sweep`

Every machine the suite builds, asked the unwebbed question.

    ⭐⭐⭐ **91% of this repository's rules are invisible to every instrument
    above.** 51 rules live in `ugm/rules/*.ugm`; **506 are string literals inside
    Python**, 360 of them in `selftest.py`. So the census, the atlas and the
    load-time note between them cover under a tenth of the corpus, and the
    numbers this module reports are about the tenth that happens to be in a file.

    This reaches the rest without moving a line, by `ugm.harmony`'s own trick:
    hook `Machine.run` and ask each machine once. And it paid immediately -- it
    found a bug **in the checker**, not in the corpora: a variable in relation
    position (`+?kind(?item)`) was being reported as a relation nothing writes,
    so a corpus using §4's *class as data* was told a working rule was broken.

    ⚠ **What it does NOT justify is moving the fixtures.** 62 of 239 machines
    report an unwebbed name and nearly all are correct about a deliberately
    partial fixture -- a rule loaded to test something else, whose premise nobody
    supplies. That is the same result the load-time note gave (91 fires, all
    correct, all useless), and externalising the fixtures would not change it.
    What externalising buys is **clarity about what is engine and what is
    corpus**, which is a different argument and a better one.

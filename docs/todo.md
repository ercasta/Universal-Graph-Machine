 I have two changes to propose, let's decide whether to do this now or later. One is syntactical: instead of rule <something>:, could we use rule(something,implies(...)) and rule(something,causes(...))? Same
  for actions: action(move(?x,?y)) where in this case ?x and ?y mean they will be bound at runtime. This would make everything be "facts". The second change is more significative. Right now we have some
  things automatically done by the engine like saving short term memory. What if we have multiple experts active in parallel, where "parallel" actually means there is an "outer loop" that make them act in a
  specific order; in particular we could have an "expert" dedicated to memorizing things, or do "accessory" work, with a separate "attention" table 

---

# Queued: retire situations, and manage hypotheses EXPLICITLY

Proposed 2026-08-20. Not started. Surveyed and measured below so that whoever
takes it starts from numbers rather than from the argument.

## The proposal

Reasoning about a scenario means **altering the actual graph**, consciously
knowing it is a hypothesis, manually mapping and storing the results and the
plan, and manually reverting the changes afterwards. The engine loses the
situation mechanism entirely: no branch per supposition, no per-situation
interning, no second identity on the node. Rules get stronger; the engine gets
much smaller.

## Why this looks right

**It is the move this repository keeps making and keeps being right about.**
Machinery that DECIDES becomes a fact a corpus reasons about. Situations are the
largest remaining piece of engine-that-decides, and 2026-08-20 retired `prefer`
and the buffs on exactly that argument.

**The dependency ratio is very favourable — engine-deep, user-shallow.**

    76 mentions of `situation` in `graph.py` alone (874 lines)
    plus per-situation interning, BOTH indices keyed by situation, two
    identities per node, `Machine.suppose`/`discharge`, `Graph.carry`,
    `Graph.branch(born=…)`, `Moment.watermark`, the situation register

...and standing on all of it:

    ugm/modality.py     one probe, and its own header says the question it was
                        built to answer has already been ANSWERED and acted on
    ugm/selftest.py     ~16 fixtures
    worked.ugm          one rule concluding `suppose(?p, likely)`
    bundle.ugm          the re-entry rules (`resume`)

No production module builds on suppositions.

**It fixes the leak the current design concedes and never fixed.** Measured, on
the three-rule fixture, leaving the hypothesis behind each time:

    supposition 1   graph 1505 -> 1679   (+174, kept for ever)
    supposition 2-5              (+95 each, kept for ever)
    visible from the caller afterwards: None    <- containment DOES hold

`docs/situations.md` predicts this in its own words -- *the graph is not
reconstructible from the deltas, so a materialisation cannot be discarded...
a long-running agent that supposes constantly accumulates them* -- and says the
fix is the replay stage, which is the one stage of four that was never built.
**An explicit revert IS that discard**, and it arrives without building replay.

**And *consciously knowing* is the strongest part of it.** `situations.md`
again, on the current design: *Today the seat is a register and nothing can
refer to it, which is why `p@current` would be unwritable.* The agent is
currently inside a hypothesis without being able to SAY that it is. Making the
hypothesis a thing the agent asserts, plans over and reverts is what lets it
answer *what would happen if we set fire to the house* as a REPORT rather than
as a side effect.

## DECIDED, 2026-08-20 — and it is smaller than the queue entry above assumed

The author's call, taken in three steps, each of which shrank the job:

    1. hypothetical reasoning is just the REGULAR GRAPH
    2. no mark/revert primitives -- reverting loses the conclusions too, and the
       conclusions are the point
    3. no branching or reverting in the CHAIN either

So this is a **deletion, not a rewrite**. Nothing replaces situations. An agent
reasons about a hypothesis by asserting it and letting the ordinary rules fire;
it knows the conclusions are hypothetical because it RECORDED that, not because
the engine hid them.

⚠ Do not re-derive `mark()`/`revert()` from the queue entry above. It was
considered and rejected for a stated reason: a conclusion written during the
hypothesis is inside the reverted region, so a revert throws away the answer it
was called to get.

### What this costs, measured rather than conceded

**Containment goes, and it is the current design's headline claim.**
`selftest.supposing` asserts *containment: nothing concluded inside is readable
as current belief* -- `symptom(pump7, restricted)` is `None` outside today. It
will hold. That check is inverted, not deleted, so the loss stays measurable.

⭐ **But the lifting objection does NOT apply, and that was worth checking.**
`suppose` exists because a generic lifting rule cannot cross rules that carry
variables. Measured, on the reified `<lift>` rule:

    generic <lift>, ground pipeline     likely(r(x))                     +
    generic <lift>, variable pipeline   likely(action(replace, pump7))   None

That would be fatal to a SCENARIO-RELATIVE replacement, which would need lifting
or per-rule scenario forms. It is irrelevant here: asserting into the real graph
means the ordinary rules fire unchanged, which is the whole appeal.

**97 `instances_of`/`instances_with` call sites** stop being scoped for free.
During a hypothesis they answer about the hypothetical world, which is intended.
It breaks only if something concurrent reads mid-hypothesis -- `probes/experts`,
`core/channels`.

### The inventory, measured

    core/graph.py    57 `situation` + 12 atom/carry/branch. TWELVE dicts keyed
                     by SituationId: _sit_parent, _sit_born, _sit_of, _vis,
                     _atom, _node_by_atom, _identity, _mentions, _interned,
                     _by_rel, _by_arg, _merged. Both indices lose a key
                     component; `_interned` becomes (rel, members).
                     Gone: branch, standing_in, _visible, visible, situation_of,
                     atom_of, node_of, identity_of, carry, rebuild.
    core/gate.py     20. Frame.situation/home and all three pin/restore blocks.
    core/machine.py  16. suppose, discharge, _hypothetical, _own_frame, _leave,
                     the situation register property.
    core/chain.py     4 + 6. ⭐ The chain goes LINEAR, so `at_or_after` collapses
                     to a depth comparison -- `resolve`'s own comment says *a
                     depth comparison cannot replace it once anything forks, and
                     supposing forks by construction.* Nothing forks now.
    selftest.py      73 `situation`, 42 `suppose(`, the whole `situations()`
                     group, and selftest.py:4024 which forks the chain ON PURPOSE.
    corpora          worked.ugm (one rule concluding `suppose`), bundle.ugm's
                     `resume` rules.

⭐⭐⭐ **`Frame` collapses to a singleton.** The engine creates exactly TWO
frames: the root register, and the supposition child. Remove suppositions and
`frame.parent`, `purpose`, `wrap`, `carried` have no second case. §18's call
stack is FACTS, not frames, so it is untouched -- check that before assuming
`Frame` can go entirely.

### Order, and there is no green state in the middle

The indices change key shape in one step or the engine does not run. This is one
large commit, not a staged landing. Do `graph` -> `gate` -> `chain` -> `machine`
-> `selftest` -> corpora, and expect red until the last of them.

### What is GAINED, so it is not only a loss

The 95-nodes-per-supposition leak `docs/situations.md` concedes and never fixed
goes away, because there is no hypothesis to leak FROM. And `docs/situations.md`
itself becomes a historical document rather than a description of the engine --
move it, do not leave it describing a mechanism that is gone.

## Two things to design rather than discover

⚠⚠⚠ **Containment stops being structural and becomes a promise.** Today it is
by construction: 106 nodes minted inside the `supposing()` hypothesis, 0 visible
to the caller. Under the proposal containment is whatever the revert actually
does, and a botched revert leaves `burnt(house)` BELIEVED -- silent, and
belief-corrupting, which is the worst failure mode available here.

> The revert must be CHECKED, not trusted. The delta chain is reified, so *are
> we back where we started* is computable. One engine check that refuses to
> continue otherwise is a row, not a mechanism -- and it keeps the guarantee
> while still deleting the machinery.

⚠⚠⚠ **Negation-as-failure and counting are the sharp edge.** `situations.md` is
explicit that stratum-0 structure is where NAF, counting and the rules-as-facts
interpreter all live, and that today BOTH indices are keyed by situation so
aggregates are scoped for free. If a hypothesis mutates the real graph, every
`unsupported` / `blocked` / count asked during it answers about the mutated
world. That is CORRECT while the agent means to be hypothesising, and wrong the
moment anything concurrent reads -- `ugm/experts.py`, `ugm/channels.py`. Decide
it explicitly.

⚠ And sibling hypotheses become a STACK rather than a tree. `Graph.branch(born=…)`
branches from an arbitrary past commit today, and `situations()` checks two
siblings building `on(b, c)` independently. Comparing two scenarios becomes
do-A, record, revert, do-B, record, compare-the-records. Probably fine, arguably
more honest, but it is a real capability change and should be named as one.

## What to measure first

How many places actually read an AGGREGATE across a situation boundary. That
number decides how much of the second warning is theoretical.

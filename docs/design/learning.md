# `learning.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Does an episode teach the next one anything? (§19, §20)

Learning here is offline and it is a **corpus**: an episode ends, `review` and
`blame` walk the trail, and `learned()` writes surface text the next episode
loads. Nothing about the loop changes. So the question this instrument asks is
the only one that matters about it -- **run the same world twice and see whether
the second run is better** -- and its gate is that the answer can be no.

    python -m ugm.learning.learning

The world is the one `forgoing2` built, because it is the only kind that can
measure a chooser: two ways to get water, and one of them breaks a jug another
goal needs. Everything upstream of forgoing was measured in a world where the
agent took the good route AND the bad one, so *choose the better rule* had no
content and an exact recall table bought nothing (`experience`). It has content
now, and the arena is a single line of authored order:

    <use-jug> written first  ->  the jug is smashed
    <use-tap> written first  ->  the jug survives

Nothing else in the corpus differs. Two thirds of this agent's arbitrations are
settled by typing order, and this is one of them, with a cost attached.

⭐⭐⭐ **What it measured, and the reason this file exists.** Blame alone does not
close the loop. An episode that smashed the jug blames the smasher and drops it
from what it recommends -- and then **smashes the jug again**, because omitting a
rule leaves it exactly where it was, first in authored order.

> **Suppression is not a decision.** It says *do not recommend this*. It cannot
> say *do that instead*, and only the second changes a run.

The missing half was already on the trail. `forgone(A, w)` records that `A` was a
live way of getting `w` and something else was taken, licensed by
`applied(<winner>)` -- so a blamed winner names its own alternatives. Joining the
two needs no new bookkeeping, which is the third time credit assignment has come
out that way. `Machine._instead_of` is the join and `_no_promotion` below is
the control that shows it is load-bearing.

## What a lesson SAYS, which is what changed (§21)

A lesson used to be `prefer(<use-tap>, water, 3)`. It named a RULE, and a rule
id is stale the moment that rule is adopted, composed or renamed -- keyed on an
identity, one level up from bindings, which is the defect this whole thread has
been about. It now names a NODE:

    fact +attention(sink, 3)                    depth 0, and ground
    { +tap($v0) } => +attention($v0, 3)         depth 0, generic
    { +precious($v1), +tap($v0) } => ...        depth 1, and so on

`sink` is what `Machine._salient` works out: the thing the passed-up route is
about and the route that harmed is not. Everything else in this file is
unchanged, because nothing about how a lesson is FOUND changed -- only what it
is written in.

⭐⭐⭐ **And the gain is not a refinement, it is a kind.** Rename `<use-tap>` in
the world the lesson is carried into and the attention lesson still saves the
jug, while the `prefer` row does not merely go inert -- **it fails to load**,
because it names a statement that is not there. Measured below.

⚠⚠⚠ **The cost is real too, and it is measured rather than conceded.** A node
can only separate two routes that are ABOUT different things. Where both routes
hold their vessel -- `holds(jug1, kettle)` and `holds(vase, kettle)` -- no node
lifts one and not the other, so the lesser of two evils, which `prefer` could
state, is now unsayable. That arm of this file is a negative result.

## `run`

Play the same world `rounds` times, each one loading what came before.

    ⚠⚠⚠ **What is carried ACCUMULATES, and it has to, which is a finding
    about the rewrite rather than a convenience.** This used to replace the
    carry with whatever the last episode wrote, and that worked only because a
    lesson was re-derived every round by CREDIT: episode 2 took the tap, the tap
    was on the support of the outcome, so `prefer(<use-tap>, water, 3)` was
    written again by a pass that had nothing to do with regret.

    Credit has no node-keyed sentence and is gone, so **an episode that goes
    well now has nothing to say** -- and replacing the carry forgets the lesson
    the moment it starts working. Measured: episode 3 smashed the jug again.

    > **A lesson learned from regret is written once. The corpus of experience
    > has to be a corpus, not the last thing that happened.**

    `keep=False` is the control, and it is this function as it stood.

## `the_lesser_of_two_evils_is_unsayable`

⚠⚠⚠ A route can only be preferred over one it is NOT about. Measured.

    This used to be `lesser_of_two_evils`, and it used to report a result: with
    magnitude accumulated across episodes the agent converged on the cheaper of
    two damaging routes, from a good start and from a bad one. That result was
    real and it is gone, because it rested on `prefer` NAMING THE RULE.

    An attention lesson names a node, and it lifts every rule whose antecedent
    speaks of that node under any relation. Here the two routes are symmetric:

        <use-vase>   goal, holds, vase
        <use-jug>    goal, holds, jug

    `jug1` is spoken of under `jug` -- which only the jug route wants -- and
    under `holds`, which both do. So attending it lifts BOTH, the walk decides
    as it always did, and there is no other node to try: the vessel is the only
    thing either rule is about.

    ⭐⭐⭐ **So `_salient` returns nothing, and that is the design working.** An
    earlier version scored candidates by *fewest of the harmed route's
    relations* and took the best available. It named `jug1`, wrote a
    well-formed lesson, loaded it without complaint, and moved nothing --
    advice that cannot be obeyed, indistinguishable from advice that works
    until you measure the run. Refusing to write it is the difference between a
    limit and a bug.

    > **Rule-keyed advice can always separate two routes. Node-keyed advice can
    > separate only routes that are about different things.**

    Returns the per-episode losses and what, if anything, was learned.

## `a_lesson_outlives_its_rule`

Carry a lesson into a world where the rule it is about was RENAMED.

    ⭐⭐⭐ **The whole argument for keying on nodes, and it is one run.** A
    rule id is not stable: rules are adopted, composed, rewritten and edited,
    and §21 is full of mechanisms that do it. A lesson that names one is
    betting on an identity.

    The measurement is stronger than *goes stale*. The `prefer` row does not
    quietly stop applying in the renamed world -- **it fails to load**, because
    `<use-tap>` is a statement reference and there is no such statement. A
    corpus of experience could be made unreadable by an edit somewhere else.

    ⚠ The rename is the whole difference. Same world, same objects, same
    authored order, one identifier changed.

## `a_learned_rule_is_a_decision_tree`

A `prefer` FACT is a decision tree of depth ZERO. A rule says *when*.

    Not an analogy. A tree's root-to-leaf path is a conjunction of tests ending
    in a verdict, which is a rule; its internal nodes are antecedent members; and
    `<relevant>` has shipped in exactly this shape since §13. Two consequences
    that were already true and unnoticed:

    * **`_priority` sums applicable rows, so preference is already an ADDITIVE
      ENSEMBLE.** A set of shallow learned rules is a forest natively -- measured
      at 4 + 3 = 7. Nobody designed it as one.
    * **Generalising is unconstrained**, because a preference consequent contains
      no variables, so the loader's bound-variable rule is satisfied by anything.
      A rule that concluded about the world would not have that freedom.

    The tests come off the trail (`_circumstances`), not from feature
    engineering: the hypothesis space is the corpus's own vocabulary.

## The VERDICT survives the rewrite and the REA

⚠⚠⚠ The VERDICT survives the rewrite and the REASON does not, which is
worth more than the number. Under `prefer` the explanation was
*`_priority` sums, and summation is not voting*: an over-general row was
ADDED to the others and could not be outvoted. Attention does not sum --
`_pull` and `_attention_weights` both take the STRONGER of two. It still
fails, and for a reason one step deeper.

> **Attention is MONOTONE.** One leaf attends the tap in B and the two
> that decline cannot take it back, because there is no sentence for
> *not this one, here*: `unattend` clears the whole queue.

Same shape as the old finding -- an ensemble's agreement is invisible and
only its disagreement counts -- arriving through a different mechanism,
which is what makes it a property of ensembling here rather than of
summation.

# Models: the core, the context, and who decides

The design conversation of 2026-08-22, after the sigil change and the gate-level erase.

Everything marked *measured* was run against the tree at `1eb0b67`. Everything else is a
position taken in conversation and is marked as such. No engine was changed to write this;
three of its conclusions are that the engine already does the thing, and one is that a
docstring points at a function that was deleted.

---

## 1. The question

A world model is not the world. It lets an agent make hypotheses, forecast, look for causes,
form expectations. Take the Tower of Hanoi and put one move — *A onto B* — into four
situations:

    in my head          I imagine an illegal move, conclude it would be illegal, take it
                        back, and try another. Nothing happens.
    with a friend       I declare the move. My friend says it is illegal. I lose the game.
    with a toy, alone   I make the move with my hands. The toy does not explode. Nothing
                        happens.
    in a tournament     I make the move. I am disqualified.

The move is stated identically in all four. The reasoning about *what makes it illegal* is
identical in all four. What differs is entirely what follows. So there is a core model of
Hanoi, and there are outer models — of playing with a friend, of a tournament — and the
outer ones must work for any game, or they are not models of *playing with a friend*, they
are models of playing Hanoi with a friend.

The engine must therefore hardcode no notion of forbidden, invalid or refused. That is the
author's position and this document takes it as given. What follows is what it costs, what
it turns out to already be true of, and where it bites.

Add a fifth situation, because it separates things the first four leave fused: **explosive
Hanoi**, a physical version where an illegal move makes the toy explode.

## 2. The core model states a verdict and does nothing

Already true, and the reasoning was already written down. `ugm/probes/hanoi.py`:

    rule <covered> = implies( { +attempt(move($d, $p)), -clear($d) },
                             { +declined(move($d, $p), covered),
                               -attempt(move($d, $p)) } )

It deposits the verdict, cancels the attempt, and stops. Its own comment gives the argument
from the other side: *before this, an attempt to move a covered disk simply matched nothing,
and "nothing happened" is indistinguishable from "nothing was wrong" — the silence this
whole design is against.*

So an illegal move is a **classification**, not a prohibition. The core model never says
*you may not*; it says *this one is covered*. Whether that costs anything is somebody else's
rule.

This is `deposit-dont-decide.md` applied to game rules, and it is the whole of the bridge
the outer models need. The inner model must supply exactly two things — a way to state a
move, and a verdict on it — and must supply no consequences. There is no special construct
for this. It is a discipline, and the discipline is the interface.

## 3. Playing in your head is already three rules

`learning/practice.py`:

    rule <act>     = implies( { +world($s), +in($s, doing($a)) },     { +doing($a) } )
    rule <assume>  = implies( { +rehearsal($s), +in($s, doing($a)) }, { +in($s, did($a)) } )
    rule <observe> = implies( { +world($s), +did($a) },               { +in($s, did($a)) } )

A scene the agent calls its world acts; a scene it calls a rehearsal assumes instead.
Containment is `+world($s)` — an ordinary premise a rule fails to match. These three
replaced `suppose`/`discharge` entirely, and they are generic over the action: they do not
know what game.

Measured: **a rule can conclude `rehearsal($s)`.** So deciding to think is authorable, not
only configurable — the agent can mint a rehearsal scene off a premise, and nothing about
that is engine work.

## 4. What the engine does hardcode, and why it is not a counterexample

The gate has a veto list and writes `refused(...)`. That looks like exactly the hardcoded
prohibition this document says must not exist. It is two other things.

- `_dispatch` is an `on_write` hook, so writing `doing(p)` **emits the act**. The veto is
  the last point before the act leaves the agent. That is an *edge*, not a claim about a
  world. The gate's own comment: *refusing here is what keeps the act inside the agent,
  rather than emitting it and regretting it.*
- The one shipped veto, `_only_among_ids`, is **well-formedness**. A relation declared
  `relationship(<rel>)` holds among things with ids, never among denotations, because a
  compound member is a criterion for picking a thing out rather than a thing. That is a type
  error — the sentence does not denote — not an illegal move.

So the engine hardcodes an edge and a does-this-sentence-mean-anything check, and no notion
of legality. The position survives contact with the code.

**But the vocabulary is wrong, and it is what makes the question keep arising.** `refused`,
`forbidding` and `veto` import a legal and moral semantics onto *this agent will not emit
this* and *that is not a claim*. The names invite the confusion. This is recorded as a
defect rather than repaired, because renaming gate vocabulary touches the log format and
should be one deliberate commit rather than a side effect of a design note. The same
mistake was propagated on 08-22 when `Gate.erase` deposited `erased(...)` following
`refused` as its precedent: the shape is right, the family name is not.

## 5. The cut is evaluate / declare / do, not core / context

The natural reading of §1 is *a core model plus an outer model keyed on context*. That
reading hides the thing that actually varies. There are three different acts over one move,
with three independent costs:

    evaluate    is this illegal?      free in all five situations
    declare     declared(me, $m)      costly with a friend, in a tournament
    do          did(me, $m)           costly with a toy, catastrophic in explosive Hanoi

The core model answers only the first. Everything else is rules over the second and third.

Two consequences the context reading does not give you:

- **Explosive Hanoi needs no new core.** Imagining stays free; only the third row changed
  price. That is why the same Hanoi model serves.
- **The friend case and the explosive case are structurally different**, not two settings of
  one dial. One keys on `declared`, the other on `did`. Context flattens them; this does not.

## 6. The verdict must range over described moves

The load-bearing choice in the whole scheme, and it is one line. Write

    implies( { +did($p, $m), ... }, { +invalid($m) } )

and planning is destroyed: the only way to learn a move is illegal is to make it. Hanoi gets
it right by keying `<covered>` on `attempt(...)`, which is the *described* move. A verdict
relation that ranges over performed moves is a core model that cannot be rehearsed, which is
a core model that only works in the one situation where it is least needed.

## 7. Whose verdict counts is the outer model's real content

*The Hanoi model, handed an illegal move, should simply state that it is illegal* is right
when you are alone and wrong as soon as anyone else is present. **The verdict is a claim by
someone.** My friend's `invalid($m)` is not mine; I may disagree. So an outer model cannot
key on `invalid($m)` simpliciter.

Which means the generic *playing with a friend* model is not parameterised by the game's
rules at all. It is parameterised by whose verdict settles it:

    alone           mine settles it, and settles nothing further
    with a friend   the other player's verdict on my declared move settles it
    tournament      the arbiter's verdict settles it and mine is not consulted

All three are game-independent, and what makes them so is **authority, not legality**. The
bridge is three relations rather than one: the move, the verdict, and whose verdict counts
here. The quest corpora already say things of the form `says(dm, ...)`, so this is sayable
today.

## 8. Steering toward deliberation

Explosive Hanoi should materialise as a belief — *I believe doing this could lead to an
explosion* — and a generic chain should steer the agent toward thinking before acting. Four
things about that chain.

**"Could" is `likely(p)`.** The uncertainty wrapper is already the representation for this
and needs no new notation. It also means acquiring the belief needs no new precedence: a
learned rule concludes wrapped, and `likely(explodes(...))` cannot fight `-explodes(...)`.

**"Think first" is a premise, never a dial.** The temptation is a deliberation budget scaled
by risk. This repository has paid for that mistake once: `weaker` was carried, composed,
printed and never obeyed, then deleted — *there are no grades*. Lawfulness settled the same
way: `lawful($a)` is a premise, never a score. So `think_first($a)` is a claim a rule
concludes and another reads, deniable and arguable.

**Danger does not determine the direction.** *Danger if I move wrong* steers toward thinking;
*danger if I stay still* steers toward acting. Both are danger and they point opposite ways,
so the discriminating premise is not the danger but **what the danger is attached to**:

    risk(doing($a), $bad)   the cost is in the mistaken act      rehearse first
    risk(delay, $bad)       the cost is in the waiting           act now
    risk(rehearsing, $bad)  the cost is in the thinking          the chess clock

The third row is not decoration. Without it, *think before acting* is unconditional and the
agent deliberates forever in any dangerous situation.

**The generic rules must not mention explosions.** The chain *risk of explosion → danger if
moving wrong → think before acting* should have its first link cut out of the generic part.
Generic:

    irreversible($h) + risk(doing($a), $h)   ->   rehearse_first($a)

and *explosions are irreversible* is one told fact about explosions, not a rule. Otherwise
you need a generic rule per hazard, and the model handles all explosions rather than all
games.

## 9. Irreversibility inverts the learning story

Where does the belief come from? Told, or learned from surprise. But in an irreversible
domain, **learning from surprise is exactly what is unavailable**: you learn the toy explodes
by exploding the toy. The learning loop this repository built runs on `deviates` and
surprise — being wrong and noticing — and that loop is unusable precisely where its output
matters most.

So the steering rules have to run on testimony, and the interesting question becomes: what is
the minimum ontology that lets *explosive Hanoi* inherit *irreversible, therefore rehearse*
without anyone writing a rule about explosions? That is the same question §8's last point
asks, arriving from the learning side rather than the authoring side.

A second limit, worth writing down rather than discovering. Rehearsing tells you the move is
illegal *according to your model*. If your model of legality is incomplete, the rehearsal
returns safe and the toy explodes anyway. So `think_first` is only as good as the belief that
the model is complete — and by the paragraph above, that belief is one the agent cannot get
feedback on.

## 10. Attending the danger does not select the safety expert

The natural implementation of §8 is frames: attend the danger, push, and let the engine pick
whoever knows about it. That is what frames are for, and it has the property the composition
question needs — **the rule that pushes never names the expert**, because *a rule that had to
name the callee would be doing the selecting.*

Measured, and it does not work on the obvious attention target. Two experts, one generic
`safety` (`risk(doing($a), $bad) -> think_first($a)`, `risk(delay, $bad) -> doing(escape)`)
and one ground `hanoi`:

    attend risk(doing(move(d1, peg_a)), explosion)  ->  hanoi   {safety: 277, hanoi: 347}

    safety's ground terms : delay, doing, doing(escape), escape, risk, think_first
    hanoi's ground terms  : attempt, clear, covered, declined, move, ok, ok(peg_a), peg_a

The domain expert wins a node that is literally about risk and explosion. And the sharpest
part: **`explosion` is in neither pool**, so it contributes zero to the pick. The safety
expert says `$bad`, not `explosion`.

The mechanism is `_terms_of`: an expert's vocabulary is its own rules' **ground** terms, and
variables are skipped. So the more generic an expert, the fewer terms it has and the weaker
its signal — and the *think before acting* expert is generic by design, because it must work
for all games. The risk claim is a bridge proposition, naming both vocabularies, so the pick
becomes a vocabulary-size contest and the larger side wins.

One corpus-level workaround: attend the bare hazard rather than the hazardous move.

    attend danger(explosion)  ->  safety   {safety: 139, hanoi: 0}

Which gives a rule worth keeping — **a bridge proposition is a bad attention target**, since
the property that makes it a bridge is what makes the pick a contest. But it is a workaround,
and §11 is the answer.

## 11. The answer is more rules, and the mechanism rewards them

The author's position, and the measurement supports it rather than qualifying it. Same
`safety` expert, same fixture, with three discrimination rules added — one classifying the
hazard, one drawing the irreversibility consequence, one linking it to the act:

    thin  safety  ->  hanoi    {hanoi: 347, safety: 277}
    thick safety  ->  safety   {hanoi: 347, safety: 832}

More rules wins, on the bridge compound §10 called a bad target.

**Competence and selectability are the same currency.** Because `_terms_of` builds an
expert's vocabulary out of its own rules' ground terms, an expert that has thought harder
about a distinction is by that very act more findable for it. There is no registration step
and no discoverability knob to drift out of sync with capability. You cannot be
competent-but-unfindable except by being general — and being general *is* being less
competent about the specific case.

**So there is no right solution to picking the wrong expert, and that is the design.** Either
the agent gets it right or it does not, and a more competent agent beats a less competent
one. The engine already committed to this in writing: adding an expert re-scores every other
one and changes which expert is picked for unrelated frames, *a feature, not a bug, written
down so nobody debugs it as nondeterminism.* Meaning is a web; adding or removing an expert
changes global behaviour.

The corollary is that generality does not lose a contest it should not have entered. A frame
that scores zero everywhere keeps the rules of the frame below, so the general case lives one
frame down rather than competing as an expert.

## 12. No inheritance between experts

The author's position: many narrow experts cooperating with frequent handoffs, and no expert
extending another. Measured — three narrow experts, then the same set with one `super`
extending two of them:

    narrow only         ->  hanoi   {hanoi: 220, safety: 81, timing: 81}
    one expert EXTENDS  ->  super   {hanoi: 139, safety: 58, timing: 58, super: 196}

Two findings, and the second was not expected.

**Inheritance wins for the wrong reason.** `super` takes the pick not because it knows more
about this but because it knows more, full stop — a slower version of the coin flip wearing
a mechanism's clothes.

**And it degrades experts it has nothing to do with.** `timing` was not inherited from and
still fell 81 to 58. IDF is computed over document frequency, so duplicating one expert's
terms into another's document raises `df` for every term they share with *anyone*, and the
weight drops for everybody. Inheritance does not merely create a fat expert; it flattens the
landscape everyone is picked from. Even `super`'s winning 196 is below `hanoi`'s original
220.

Read the other way this is an argument *for* narrow experts rather than merely against
inheritance: more experts means a larger `total` in `log(total/df)` and a smaller `df` per
term, so discrimination sharpens as they are added.

**Done, 08-22.** `extends` is deleted — the reserved name, the surface sugar
(`expert geometry extends arithmetic`), the vocabulary-gate entry, and the `<inherit>` rule
in two probes. The old spelling now fails at load with a message naming the replacement
rather than parsing into something subtly different. Suite 557/0, experts 15/0, frames 21/0.

What the probes lost was three checks about inheritance; what replaced them is a check that
the pools are **disjoint**, plus its other half — *and that is a cost, not free: geometry
cannot double, so an expert needing another's work must hand off rather than absorb it.*
The second half is what keeps the first honest, since disjointness alone passes on three
empty pools. Kill-probed: giving geometry `<double>` back fails both.

**An earlier draft of this section said the discipline was "minimise overlap", and that was
too blunt.** Measured, and the correction matters for how corpora get written:

    narrow only                    hanoi 220, safety 81, timing 81
    + a universal rule in all 3    hanoi 220, safety 81, timing 81    unchanged
    + safety's own rule in timing  hanoi 220, safety 81, timing 162   timing now beats safety

**Sharing a rule every expert holds is free.** Its terms get `df == total`, so
`idf = log(total/total)` is zero and they contribute nothing to any pick. **Sharing a
discriminating rule is the inheritance problem in miniature** — the borrower wins the
question it borrowed, and here `timing` ends up outscoring `safety` on safety's own subject.

So the rule is not *overlap as little as possible*; it is **share only what everybody
shares**. That is also what made the deletion cheap: `extends responder` existed so every
expert could return, and `<replied>` is universal, so writing `fact +knows(X, <replied>)`
three times costs exactly nothing.

**Frequent handoffs are free; deep ones are not.** The frame stack is bounded at 8 and the
refusal is deposited, so nothing fails silently. Push, resolve, pop, push again never
approaches it. A chain of narrow experts each consulting the next before the last has popped
is depth, and that is the one shape this architecture could walk into the wall with.

## 12b. Scope: there was no scoping problem

A model reasoning about the Tower of Hanoi should work on **this** game, not on every Hanoi
game in the graph. That question ran through four proposed mechanisms and ended by retiring
all of them.

The failure is real. One rule, two games:

    rule <move> = implies( { +on($d, $from), +clear($d), +clear($to), +peg($to) },
                          { +lands($d, $to) } )

    shared disks, parts unstated     lands(d1, b1)     lands(d1, b2)          2 crossings
    distinct disks, parts unstated   lands(g1_d1, b2)  and three others       4 crossings
    parts STATED                     lands(g1_d1, b1)  lands(g2_d1, b2)       none

The middle row is the one worth keeping. *Two games cannot share disks* is true and is not
the fix: giving each game its own disks made it **worse**, four crossings instead of two,
because the pegs are still just pegs. `peg(b2)` says b2 is a peg; nothing says which board it
is on. The rule asks for a clear peg and b2 is one.

The third row is one premise per bound part — `+part($d, $g), +part($from, $g),
+part($to, $g)` — and it is exact.

So: **there was no scoping problem, there was a modelling omission.** A game is an entity
with parts. Said in the corpus, the rules read it like any other premise. Unsaid, no engine
mechanism can recover it, because the information is not in the graph at all. That is the
same construct `docs/world-model.md` already names — *a span is an identified set of
entities and relationships that can be treated as an entity; a car is an entity and it also
has wheels* — and the same principle as `wanting.md` 7's *the desire is an entity*.

### Four mechanisms retired, and why each looked plausible

**Containment / hyperedging as a new capability.** Already present: a compound node is an
n-ary edge, `_contents` reads it (*a moment holds what is asserted there, and anything else
holds its own members*), and `in($s, p)` is containment with `in` an ordinary corpus
relation, not one of the reserved names. Nothing to build.

**An expert that sets a containment and resets it afterwards.** This is `suppose`/`discharge`,
deleted on 2026-08-20. `learning/practice.py`: *a rehearsal used to be a supposition: the
register stood inside a frame... None of that exists now. A rehearsal is an ANCHOR and
containment is a premise rather than a mechanism.* A mode is engine state no rule can read,
date or deny.

**Pointing an expert at a root node.** A frame already says what the agent is about, and
deliberately does not scope what its rules match. Making it scope would be ambient state
again — a rule meaning different things depending on what is pushed.

**Discarding applications that do not intersect attention.** Measured, and it fails twice
over. See below.

### Attention orders; it cannot gate

    partial intersection on bindings     CRASH -- a rule never applies, learning dies
    same, with a fallback when empty     CRASH -- the set is not empty, it is full of dead candidates
    prefer attended survivors, else all  557/0, narrowing 7259 times, falling back 367 times

The mechanism: **attention proposes, `_survives` disposes.** `_attended_first` orders, and
the loop takes the first survivor. 367 times across the suite every attended candidate is
spent, passed up or quiescent, and the right move is one attention never named. Ordering
lets it through; filtering deletes it before the survival test runs.

The third form passes and is still not worth adopting: `_attended_first` already sorts
attended-first, so preferring them walks the same candidates in the same order. It changes no
outcome.

And gating could not have scoped anything anyway. **Ordering eventually reaches everything**
— it changes *when*, never *whether* — so it can defer the cross-game derivation but not
prevent it. Only a premise makes a match fail.

### What attends, corrected

An earlier draft of this section said attention grows to include whatever an application
touches. **It does not.** `_attend_written` attends only what a move WROTE, plus deliberate
`attend`. What it does do is decompose the conclusion, so `lands(d1, b1)` pushes four nodes:
the proposition, the relation atom `lands`, and both arguments.

Which of the four earn their place:

    whole proposition only        557 checks, 1 failing
    no relation atom, no whole    557 checks, 0 failing
    bare individuals only         557 checks, 0 failing

The arguments are load-bearing — `_attended_first` ranks bindings and a binding is an
individual. The relation atom and the whole proposition are distinguished by **no check in
the suite**. That is half of what enters a bounded, displacement-decayed queue whose own
docstring records being backed out twice because *a queue permanently full of undifferentiated
nodes made the agent chase its own tail and quiesce 30 moves early.* Not evidence that
removing them helps — no check can see the difference — but a candidate with a prior behind
it.

The residual leak, once the relation atom is gone, is the shared entity: a conclusion's
arguments are attended, and `d1` really is an argument of something the agent concluded. That
is the modelling omission again, arriving from the attention side.

## 12c. Named slots on a global anchor — expressible today, entirely

The author's, 2026-08-22, after the pointer-list proposal was scored against §4's register:
*instead of positions, named slots — `+game(_attention, $x)` in the RHS, with `_attention` a
global-variable-like node.* `ugm.probes.slots`, 9/0.

**Nothing here needs an engine change.** A slot is an ordinary proposition whose first argument
is an ordinary atom. `_attention` is not a reserved name and does not have to become one; the
`attention` relation the machinery writes is a different node and there is no collision. No
notation, no branch, no row.

Three things it buys, measured:

- **It does not read position.** Writing two slots in either order gives the same answer. The
  contrast is against the real alternative rather than a straw one: `push($a, $b)` reads left
  to right and position is the gradient, so naming the same two nodes the other way puts a
  different node in front. Both measured side by side.
- **It fuels the attention stack that exists rather than sitting beside it.** A rule that
  writes a slot puts the VALUE on the queue, through `_attend_written`, with nothing added for
  the purpose.
- **The fixed-arity antecedent is available now.** A competence rule rewritten slot-relative —
  `+at(agent, $r)` becoming `+here(_attention, $r)` — answers identically on the same world.
  That is the property the learning proposal needs, and it needs no build to have it.

Three things it costs, and the third is the one to decide deliberately:

- **A slot is not single-valued.** Two writes leave two values held; nothing in the notation
  says otherwise. The discipline is a rule the corpus writes — a three-member setter that binds
  the old value and denies it, with a distinctness computator the corpus registers. Measured
  working. That is the right home for it, but it is a rule per slot.
- **The anchor riding the queue costs nothing where it is scored.** This was written up
  first as a leak, and the author's objection was right and is sharper than *almost zero*.
  `_idf` is `log(total/df)`, so a term in EVERY expert's pool has idf **exactly 0.0**, and the
  anchor is in every pool by construction — that is what makes it an anchor. Measured beside
  the discriminating terms:

      idf  0.000   here          <- the slot relation, shared by both experts
      idf  0.000   _attention
      idf  0.693   wet / slip / dark / trip

  **And it does not reach the shortlist at all**, which is the stronger half. `_attention_asked`
  is claimed-vs-derived, not weighted-vs-plain — *someone saying attend to this is a reason to
  bring rules to mind; the machinery noticing this just happened is not*, and conflating them is
  what quiesced the dungeon 32 moves early. `_attend_written` pushes without claiming, so every
  node a slot write puts on the queue is invisible to what decides which rules are matched:
  queue `['chess', '_attention', 'game', 'game(_attention, chess)']`, shortlist `[]`.

  So §12b's relation-atom leak does NOT arrive from a third direction here. What is left is
  arithmetic rather than credit: queue **space**. `_push_attention` moves a repeat rather than
  adding it, so the anchor costs exactly **one** slot however often it is written — measured —
  though each distinct slot relation costs one more, against a span of 7.
- **Scope is traded, not gained.** The queue is per-frame — a push suspends it, measured — and
  a slot is global, readable from inside any frame. Two lines of work naming one slot share one
  cell. That is §12's *share only what every expert shares* one construct along: a slot name
  every expert uses the same way is free, and a slot name two experts mean differently makes
  the borrower read the lender's value. **Decided: global.** See below.

### Global was chosen, and what the mitigation actually is

The author's call, 2026-08-22, and the argument is from expressibility, which is this
repository's standing criterion:

> *Rules have no notion of local. When a rule queries something, it always queries global.
> Global makes nothing impossible; per-frame might. It only poses an increased risk of confusion
> or conflict, even between multiple instances of the same expert.*

That is the right shape of argument — a mechanism that forecloses is worse than one that
confuses, because confusion is a modelling problem and foreclosure is not. What follows measures
the risk and the mitigation, because a mitigation that is assumed is a mitigation that is not
there. `ugm.probes.slots`, checks 9 through 13.

**The risk, plainly.** A lone slot member fires on every value in the cell — `visited(hall)` and
`visited(cave)` from one rule — because nothing in the rule tells one value from another.

**The obvious mitigation is not the one.** *Join the slot to something anchored* — which is
`_stored`'s own discipline, **bounded by something already known** — does **not** isolate over a
shared world, because the foreign value has something to join to as well:

    rule <joined> = implies( { +here(_attention, $r), +wet($r) }, { +slip($r) } )
    ->  slip(hall) AND slip(cave)

Measured, because it is the first answer anyone reaches for. It isolates only when the foreign
value has nothing in the world to join to, which is a much weaker guarantee than it sounds.

**The mitigation that does work is the expert pick**, which is what the author named. Two experts
using the same slot name are still told apart, because what discriminates is the rest of their
pools — and the anchor and the shared slot name, both at idf zero, do not blunt it:

    pick on wet(hall)     safety 69, gloom 0

So **isolation moves from the data to the pool.** The value is global; which rules may read it is
not. That is a coherent division rather than a concession: the slot is shared state, the pool is
per-frame, and the frame was never the thing being given up.

**And it cannot help two instances of the same expert**, which the author named as the residual.
One pool, one set of rules, one cell — and the instance is nowhere in the answer:

    two instances, one cell     may(hall, north), may(cave, down)

**The crossroad pattern, and why it needs nothing built.** The anchor is an ARGUMENT, so a
private space is the same construct with a different first argument. One rule takes from the
crossroad and denies it:

    rule <take> = implies(
        { +arriving($who, $r), +here(_attention, $r) },
        { -here(_attention, $r), +here($who, $r) } )

    ->  may(inst1, north), may(inst2, down)      and the crossroad left holding: - , -

That is the author's *temporary value-passing crossroad, moved to a private space almost
immediately*, and it costs one rule. **The healthy pattern is not joining, it is moving** — and
the crossroad ending EMPTY is what makes it a crossroad rather than a second home for the value.

**On the phrase *the anchor is an argument*, which was not clear.** It means only this:
`_attention` sits in an ordinary argument position, so `here(inst1, hall)` is the same
proposition with a different first argument and needs nothing new. It says nothing about how
anything is anchored across ticks, and reading it that way would be reading a claim it does not
make.

### What bridges ticks is `_attended_first`, and it is already built

The author's, on being asked exactly that: *only attention bridges over ticks, and my solution was
to choose the bindings of rules to actual graph nodes based on attention partial overlap — so if
there are two `game` nodes, one attended and the other not, the next tick should bind the rule
application to the attended one.*

**That is `_attended_first`, in `core/attention.py`, and it ships.** It sorts a rule's
applications by the summed, position-weighted overlap of the values an application **binds** — not
of the rule's terms — and the loop's own comment says what it repairs: *it takes the first
survivor and breaks, so the binding was decided by the walk.* Measured on the author's own
fixture, two `game` nodes and one attended:

    nothing attended    moves(bob), moves(alice)
    attend chess        moves(alice), moves(bob)      <- the binding flipped

And a slot WRITE is enough to do it, with nothing attending explicitly, because `_attended()` is
the whole queue and derived pushes are in it — the asymmetry that makes named slots work, since
the same push is invisible to the shortlist (4c) and visible to the binding.

**And ordering IS selection once the world moves — which the first write-up of this got
backwards.** On a frozen world run to quiescence both bindings are eventually taken, and *so
attention does not isolate a global cell* was concluded from exactly that: a fixture that cannot
move, measuring a mechanism whose whole subject is movement. The author's correction: *if the
world and the attention move, the loser will never be chosen; it will only be chosen if the other
node is attended.* Both halves measured, by letting the rule spend a shared premise:

    world FROZEN  attend chess    moves(alice), moves(bob)     <- the fixture, not the mechanism
    world MOVES   attend chess    moves(alice)                 <- the loser is never chosen
    world MOVES   attend go       moves(bob)
    ...premise returns, attend go   moves(alice) -> moves(alice), moves(bob)

So *attention orders and cannot gate* and *the other one never runs* are both true at once, and
there is no contradiction: **the exclusion is the world's, not the mechanism's** — which is why
none of the four retired gating mechanisms was needed to get it. For a global slot this is the
whole isolation story: a stale value is not read because nothing is attending it, and it becomes
readable again exactly when something does.

**The one real limit** is that attention can only move a binding **that has not happened yet**.
With the reader rule authored before the writer, the reader applies on the first tick and the
slot write changes nothing. The two halves of that check differ only in authoring order, and a
check written in one order alone would have measured the order and reported the mechanism.

### The queue is empty only at the very start, because computation begins with an ARRIVAL

The author's, on the tick-1 limit: *in real situations computation would usually start because
something has arrived on a channel, and those nodes should be attended — guiding the selection of
the first expert.* Half of that is already true and the other half is one rule, so it is worth
being exact. Measured, `slots` 19-20:

    queue at delivery       []
    queue after intake ran  ['+', 'chess', 'game', 'game(chess)', 'user', 'says']

**An arrival does not attend when it lands.** `_report` writes `arrived(...)` straight through
the gate, and that is not a move's `wrote`, so `_attend_written` never sees it. One tick later the
intake rule turns the report into an utterance, and THAT write attends every node the arrival was
made of. So the channel does seed attention, at the cost of a tick — and the *empty queue orders
nothing* limit bites only at the very start of a run, not wherever a fixture happens to begin.

**What no arrival does by itself is choose the first EXPERT**, and that is deliberate rather than
missing. The engine's only `_push_frame` call is a rule spending `push`, whose own comment says
why: *the nodes are the host rule's own variables, bound by the move that spent this — and the
expert is computed from them, never named.* A rule that had to name an expert would be choosing
the callee, which is the thing selection exists to do. So an arrival steers the first pick exactly
when a corpus rule pushes on the nodes it seeded — one rule, not an engine change — and the pick
over those nodes does discriminate (safety 69, gloom 0).

**And *authored first* is a symptom, not the cause — nothing is pre-bound.** Asked whether
binding happens during the tick or before it, the trace answers: `match` runs INSIDE the per-tick
loop and `_attended_first` reorders what it returns, every tick.

    tick 1: <focus>  binds=[chess]         attention=[]
    tick 2: <focus>  binds=[chess]         attention=[]
    tick 3: <play>   binds=[alice, chess]  attention=[chess, _attention]
    tick 4: <play>   binds=[bob, go]       attention=[alice, moves]

The same rule binds `chess/alice` on one tick and `go/bob` on the next, which no cached binding
could do. What the authoring order decides is only **which rule gets tick 1**, and tick 1 is
walk-ordered whatever runs there, because `_attended_first` carries its own guard — *nothing
attended is in play here; do not touch the order.* **An empty queue orders nothing.** So the limit
is not pre-binding, it is that attention cannot rank what has not been attended yet — which is
*only attention bridges ticks* read from the start of the run rather than the middle.

**What is still open, and it is small.** The take rule binds `$who` from `arriving($who, $r)`, so
the instance comes from the premise that occasioned the work rather than from anything the
machinery holds. Whether an instance can always name itself that way is a modelling question, and
§12b's answer to the last four of those was that the mechanism was never the missing piece — so
the burden is on a corpus that cannot do it, not on a mechanism to prevent it.

**The correction is worth keeping as a correction.** The first write-up of this section called
the anchor a leak and cited `_attend_written`'s *queue permanently full of undifferentiated
nodes*. That docstring is about a queue that decided which rules were matched, and the
claimed-vs-derived split was the repair for exactly that. Quoting the disease after the cure
shipped is how a retired hazard gets re-argued — the check that measures it is `slots` 4b/4c,
and both had to be run before the sentence was safe to write.

**~~What this does not settle.~~ Settled below: global.**

## 13. What is settled

- An illegal move is a classification, not a prohibition. The core model deposits a verdict
  and supplies no consequence. That discipline is the entire interface between models.
- The engine hardcodes an edge (where acts leave) and well-formedness (whether a sentence
  denotes), and no legality. The position holds.
- The gate's vocabulary — `refused`, `forbidding`, `veto` — imports the wrong semantics and
  is a naming defect, now propagated into `erased`.
- The cut is evaluate / declare / do, not core / context. Explosive Hanoi changes the price
  of one row and nothing else.
- A verdict ranges over described moves. `attempt`, never `did`.
- Outer models are parameterised by whose verdict counts, not by the game. Authority, not
  legality.
- `think_first` is a premise, never a budget. What steers is what the danger is attached to,
  in three rows including the cost of thinking itself.
- Generic steering rules name no hazards. *Explosions are irreversible* is a told fact.
- Learning from surprise is unavailable in irreversible domains, which are the domains where
  the steering matters. Testimony carries it.
- There is no right answer to expert selection, and that is the design. Competence and
  findability are one currency, so discrimination rules are both the epistemic and the
  mechanical answer.
- Scope is modelling, not mechanism. A game is an entity with parts; stated, the rules read
  it as a premise; unstated, nothing can recover it. Containment, root nodes and attention
  gating were all attempts to invent a fact nobody had written down.
- Attention orders and cannot gate. It changes when, never whether, so it can defer a wrong
  derivation but never prevent one.
- No inheritance between experts. Share only what EVERY expert shares — a universal rule
  has idf zero and is free; a discriminating one duplicated makes the borrower win the
  question it borrowed. `extends` is deleted.

## 14. What is open

1. **Rename the gate family.** `refused` / `forbidding` / `veto` / `erased` say *prohibited*
   about things that are *not emitted* and *not well-formed*. One deliberate commit; it
   touches the log.
2. **`_forbid` is deleted and four places still cite it as the live mitigation** —
   `machine.py:1606` (which is `_pick_expert`'s own docstring), 1763, 3534, and
   `selftest.py:6579`. The argument survived the move into the trigger seam; the pointer did
   not. Small, and worth doing before anyone reasons from it.
3. **Nothing connects irreversibility to rehearsal.** `rehearsal` works, and the choice of
   scene is made by whichever rule happens to name `world` or `rehearsal`. §8's chain is
   writable but unwritten, and it wants a fixture where getting it wrong costs something the
   probe can see.
4. **Whose-verdict-counts has no fixture.** §7 is the least tested claim in this document.
   The quest corpora have `says(...)`, so the pieces exist; nothing composes them into a
   generic play-with-a-friend model over two different games, which is the actual test.
5. **The three-row danger table has no corpus.** Especially the third row: an agent that
   deliberates forever is the failure mode, and no fixture can currently exhibit it.

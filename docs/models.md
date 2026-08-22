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

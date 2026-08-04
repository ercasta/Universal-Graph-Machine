# Advice that constrains a sequence

**Status: not built, and not started.** This is a design thread, written down so the argument is not
re-derived. It began as a note in `docs/TODO.md`, reproduced verbatim at the end.

The question in one example: *"let's plant this nail by taking turns hammering."*

Everything the system does today with advice is about **one action** — is this step forbidden, is it
preferred, does it satisfy the goal. *Taking turns* is not about any one step. It is a property of the
**order** of the steps, it is stated in a shorthand that has to be expanded before it means anything
operational, and it can equally be *recognised*: given a sequence in which two agents alternate, the
right conclusion is that they are taking turns.

That is four separate demands, and they are worth keeping apart because three of them are nearly free
and the fourth is the only real gap.

## 1. Expansion — probably already a method

*"Taking turns"* is shorthand for a longer description. The obvious reading is that the planner must be
able to *expand* it, and the obvious mistake is to add a CNL family for expansion.

Two things say otherwise. **The CNL cannot grow itself, on purpose** — adding a block verb is an edit to
`intake.py` forever, so the family count is a budget, and *relate it in the web* is usually both the
cheaper and the more principled answer. And **methods already exist**: `method.step` appends to an
ordered edge, so declaration order *is* the `then` order, free, and `steps_of` reads it back.

So the first move is a probe, not a design: **write "taking turns hammering" as a method with ordered
steps and see what is actually missing.** The project's own standing advice applies — *test the claim
before building the fix for it* — and it has been right three times in a row.

What a probe would likely find missing is not the expansion but the **binding**: a method's steps are
about roles, and *taking turns* is about two role-fillers alternating, which is a constraint over the
steps rather than a step.

## 2. Checking the order — the plan already records it

*"The respect of taking turns can be checked by checking the sequence of actions in the plan."*

**This needs no new representation at all.** A workbench keeps the whole movie: frames in order, each
with a `via` transformation naming the function it applied and the mappings it bound. `chain(frame)` is
the sequence, nearest-first, and the arguments are recoverable from each transformation's `arg`
bindings. A predicate over the trajectory has something to read today.

What it does not have is a **place to be said** — see §4.

## 3. Recognition — this is what demand-driven derivation is

*"If there is something before-after I could dynamically attribute the meaning of becoming, without
materializing extra arcs."*

That is a description of how this system already works. Derivation is demand-driven, a reader records
nothing, and predicate dispatch already lets one name have several bodies with the world choosing —
which is the mechanism for *a sequence in which two agents alternate counts as taking turns*.

The direction worth noticing is that **recognition and prescription are the same predicate read two
ways**. A guard that admits a step because it keeps the alternation, and a conclusion that a past
sequence *was* an alternation, are one condition over a trajectory. If the predicate exists once, both
readings come free, and building them separately would be the duplication this codebase keeps refusing.

## 4. The one real gap: a constraint over the ORDER of actions

Goals are **constraint nodes over states**, and `unmet` drives means-ends toward states. There is no
form for *the plan must alternate agents*, and nothing in the planner would read one. This is a genuine
capability gap and it is now recorded in [limits.md](limits.md).

The shape of the gap, stated precisely so a design has something to aim at:

* A constraint today is checked against **a world**. A sequencing constraint is checked against **a
  path through worlds** — the frame chain — so its subject is a different kind of thing.
* It must be checkable **incrementally**, at the moment the next action is chosen, or it is useless for
  search: a constraint that can only be evaluated on a finished plan prunes nothing.
* A violated sequencing constraint should behave like every other failed guard — become a **want** that
  can be planned toward, not a refusal. That is predicate dispatch slice 4 (`wants_that_unblock`), which
  this thread promotes from *a capability we might add* to *the mechanism this needs*.

## 5. Caching a derived meaning — do not build a TMS

The note proposes "crystal edges": cache a derived conclusion with a dependency that breaks it if the
world it was derived from changes, plus a *not*-trigger for the negative case.

**That is a truth maintenance system, and this project deleted all of its retraction/TMS machinery
once already**, deliberately (`REVISION 01 — standing circuits`). The recorded stance replacing it is
that derivation is demand-driven and **absence decides** — an agent, not a theorem prover. The note
itself finds the classic reason those systems grow without bound: *you cannot hang a dependency on
something that is not there*, and the fix (install a trigger on the node that is not there) is the first
step down the road that made them unmaintainable.

**Recommendation: recompute on demand.** Treat caching as a *measured* optimisation, not a design
commitment: if re-derivation ever shows up in `python -m ugm.bench`, that measurement decides it — the
same standard `workbench.index` was held to, where a stored reference was added because a walk had been
measured at 30×, not because it looked slow.

## What this thread does to the plan

It **does not change the current arc**, and it is the strongest argument yet for finishing it. The note's
own third paragraph is the reason: *"the planning machinery must support the verbs in which the other
rules are expressed."* A Python `_PHASES[phase]` cannot consult a prescription written in the web, so
this is unbuildable until the plan-act-check loop is data — which is exactly what
[HANDOFF.md](HANDOFF.md) items 3 and 4 are.

What it does change is the ranking of what comes after: **predicate dispatch slices 3 and 4 move up**.
Slice 3 is conditions that speak of the ambient goal, reached by walking the activation chain; slice 4
turns a failed condition into a subgoal. *"At each step I have to check I am not violating anything
and/or respecting the advice"* is those two mechanisms and not a third one.

## The note as written

> considering words have synonyms and or "expansions" e.g. "taking turns" is a shorthand description for
> something that takes a lot more words and expressions to explain, during planning, should we allow
> "exploring" the rule space considering expansions and synonyms too? e.g if i say "let's plant this nail
> by taking turns hammering", the plan should "expand" the "taking turns". This example is particularly
> juicy because it constrains the SEQUENCING of actions, so it's not just a matter of vetoing or
> prescribing a single action. The respect of the property of "taking turns" in a plan can also be checked
> by checking the sequence of actions in the plan.
>
> It's more like at each step of deciding the next action in the plan i have to either check i am not
> violating anything and / or I am respecting the advice, so the "planning machinery" must check not only
> the "expert guidance" but also the prescriptions.
>
> It becomes EXTREMELY important that the "planning machinery" "supports" the verbs in which the other
> rules are expressed, e.g. "taking turns" might use "first", "next", etc. This could be implemented by
> dynamic dispatching or by "overlaying" the plan with "meaning-compatible" edges.
>
> It could also be the other way around i.e. dynamic meaning recognition: if there is something
> "before-after" I could dynamically attribute the meaning of "becoming", without materializing extra
> arcs. And this dynamic meaning recognition could of course benefit from the dynamic dispatch.
>
> (note that in general this would also allow concluding than two players are "taking turns" when we have
> a sequence of actions in which they alternate). And once we have deducted this "extra meaning" for a
> part of the world, if that part of the world "does not change" (we could create "automatic" "crystal
> edges" that break the deduction if something in the world that was used to deduce it changes - but it
> does not play well with "not" conditions because we can't "crystal edge" something that is not there -
> BUT we could install a "not" trigger on the node...)

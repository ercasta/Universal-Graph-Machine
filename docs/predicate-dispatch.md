# Predicate dispatch

**A design note. Slices 1 and 2 are built** — a function states its conditions in its own `.mf` source,
several bodies may share a name, and which one a call means is decided by evaluating those conditions
most-specific-first. Slices 3 and 4 are not. The rest of the note is the argument, and it is kept because
the argument is worth more than the conclusion.

> ⭐⭐ **A guard is missing its addressing half, and that is why `select` goes quadratic.** A criterion in
> `criterion.py` says *where to look* before it says *what must hold* — `wants <sort> <label>` — and
> `precedence._covers` opens by comparing exactly that: *"keying differs first: two rules that watch
> different constraints never compete for a situation."* A **function** body carries only `test` edges,
> so both sides answer `None`, the early-out is vacuous, and every body must be evaluated. Measured, all
> bodies applicable: 10 → 0.82 ms, 50 → 18 ms, 100 → **63 ms**. Two fixes, both cheap. The order
> `_covers` computes is **static** — no arguments, no frame, no call data — so `select` rebuilds per call
> what `function.define` could decide once, exactly as it already does for `mediated`. And giving a guard
> the *where* it lacks turns the comparison into an **index**. See `docs/comparison.md` §Language: the
> same change buys the *"which tokens do I look at"* semantics a construction grammar needs, with no part
> of speech anywhere, since the address is whatever attribute the rule watches.

## Why dispatch, and not a bigger vocabulary

The decisive argument, and it is not about elegance. Without dispatch, a domain that draws a distinction
must **mangle names**: `go_to_river_bank` beside `go_to_financial_bank`. Two problems, and the second is
the real one.

The count multiplies. Senses × verbs, a name per combination, and every new distinction re-crosses the
whole vocabulary. The CNL cannot grow itself on purpose — a family is an edit to `intake.py` forever — so
a design that answers ambiguity by adding names is answering it with the budget that has none.

**And a mangled name is an island.** The distinguishing condition ends up baked into an identifier, where
nothing can read it: nothing can ask *what makes this the river sense*, nothing can plan towards making
it true, and the relation between the two senses is gone — they are two unrelated names that happen to
share a prefix. That is exactly the argument [mediated-access.md](mediated-access.md) makes one level
down for lowering to a **name** rather than to an opcode (*"the relation is gone as a relation; nothing
can ask what the rule was about, only what it stepped through"*), and it lands the same way here: an
island is created by the second caller. Dispatch keeps the condition as **data** and the senses related
by sharing a name.

**What the spike found**, since two of the three things were not in the plan:

* **The condition language had no way to say `x is y`.** Four test sorts — `exists`, `type`, `attr`,
  `link` — and none of them relates two references by *identity*, which is the very first thing a guard
  wants. Added as `same`, with the precedent already in the building: `path.py`'s rule is that `is`
  compares identities and everything else compares values, and `types.Rel` has carried `is` / `is not`
  inside a schema all along. It was missing exactly where two *arguments* meet, which is the hole.
* ⚠⚠ **`x is y` already parsed, as a link whose label was `is`.** Three words with `is` in the middle
  fell through the shared proposition grammar to the bare link form, producing a condition that matches
  nothing, silently — the *parses, runs, means the wrong thing* verdict, reachable from the day the
  grammar was shared, in every family that uses it. `_shape` recognises it now and each reader states a
  position: a condition builds it, a goal refuses it (nothing can make two individuals into one), a
  method step refuses it.
* **The blanket rule was not a correctness rule.** It read as one, and its own comment called it one. But
  `connect(a, b)` making a self-loop is an ordinary thing for a domain to want, so *no node in two roles*
  was a **domain assumption living in the planner**. Authored, it is the domain's again — and the check
  that proves it is the control: an unguarded two-parameter operator is still offered one node twice.
* **It cost nothing measurable.** Sussman: 50 imagined states and ~1050 ms, both unchanged. The guard is
  evaluated after the parameter-type gate, so most calls never reach it.

The proposal: **a name resolves to an implementation by evaluating a condition over its arguments and
their surroundings**, not by matching parameter types alone. The condition is the one a criterion already
writes — a boolean expression that may reach linked nodes, walk a relation transitively, draw a candidate
from a set, and relate two arguments to each other.

## The evidence that this is a real gap, not a nicety

Not an example anyone constructed. `driver.enumerate_frame` builds the cartesian product of type-valid
bindings and then says:

> minus the ones binding one node to two parameters — which is not a heuristic but a correctness rule for
> operators like `stack(b, onto)`, where the type system cannot say `b ≠ onto`. `types.py` validates one
> argument at one call site by design, so **a relation *between* parameters has no declared form** and has
> to be enforced here or in the body.

A correctness rule about `stack` is written in Python, in the planner, because the declaration language
cannot hold it. That is an island of exactly the shape the audit went looking for, and it has been
sitting in the search loop being described rather than closed. It is also the cheapest possible first
consumer: `fn stack(b, onto) unless b is onto` deletes a hardcoded line.

## What already exists

The idea is less of a leap than it looks. Four pieces are in place and were built for other reasons:

| | |
|---|---|
| dispatch on one parameter's type | `selection.candidates` — functions whose single declared type validates for a node |
| dispatch among several bodies by condition | `function.applicable` — picks a **mock outcome** by testing arguments against parameter types |
| a condition language that reaches the surroundings | `criterion.py` — `when` / `unless`, four test sorts, paths of any depth, backward hops, transitive reach, set draws |
| an order over competing conditions | `precedence.py` — authority → force → **specificity** → random, with `_covers` comparing whose conditions are tighter |

And the surface costs nothing new. `intake.py` parses a goal line and a criterion condition through **one**
proposition grammar — `_shape` and `parse_link` serve both — so `when d.of is a river` needs no new CNL
family. That matters more than it sounds: adding a block verb is an edit to `intake.py` forever, so the
family count is a budget, and this proposal spends none of it.

The single choke point is `function.find`, which maps a name to one function node by scanning for it.
Predicate dispatch is that function returning **the most specific applicable body**.

## The prize is not dispatch. It is a new kind of subgoal.

The obvious reading of this proposal is "richer polymorphism". That is true and it is the least
interesting part.

`driver.wants_that_unblock` derives *what would have to become true for a blocked-but-relevant action to
become possible*, and it derives it from **parameter type failures**. That component is what makes the
guided cost flat instead of growing 4 / 6 / 10 / 16 with library size, measured. A guard is strictly
richer than a type and is still data read the same way — so the same reader extends to it, and
*"`go` cannot mean the river sense here"* stops being a dispatch outcome and becomes **a thing the
planner can plan towards**.

That is the argument for building it. Sense selection is the demo; means-ends chaining through a
condition that is not a type is the capability.

It cuts the other way too, and honestly: `driver.establishes` walks a stored body to learn what a rule
writes, and a name denoting several bodies forces a union — an over-approximation, legal by contract, but
one that degrades ranking. **A static reader that loses information gets slower before it gets wrong**
(disabling `access.as_opcode` took the suite from 59 s to minutes with no wrong answer anywhere). The
guards add more than the union removes, probably. That is a guess, and it wants `python -m ugm.bench`,
not an argument.

## Sense selection, and the half of it the arguments cannot see

*Go to the bank* versus *go to the bank of the river*. The sense is expressible today, because a type is a
structural subgraph schema and `recognize` is bottom-up with nothing stored:

```
declare_type(g, "river_bank", {"of": Req(kind="river")})

fn go(d: river_bank)     when ...
fn go(d: financial_bank) when ...
```

So the sense is decided **by the world, not by the word**, which is the right stance and the one this
codebase already takes.

⚠ **But the sense is often not in the argument at all.** *"I need cash, go to the bank"* is disambiguated
by the discourse, and no amount of looking at the bank will say so. The remaining half is the ambient
situation — what are we doing, under which goal — and it is already reachable: `criterion.py` keys on
`goal.ancestry`, walked from where the call is.

**Dispatch on the arguments *and* on the situation, with the situation reached by walking the chain,
never by marking the nodes.** The second half of that sentence is a scar. `dispatch.service` decided *am I
imagining?* by testing whether its argument was a workbench copy; that was the same question only while
planning handed rules copies, and the moment rules were bound to real nodes the guard went quiet and a
plan really listed a directory. A guard that tests a *value* for a fact about the *context* is right by
coincidence. Marking nodes with a `plan` attribute to steer dispatch would be that mistake again, and
worse: the search holds many frames alive at once (**16 of 17 stepped frames fork**), so *"this node is
being planned over"* is not a fact about the node, and an attribute that tried to be would have to be
versioned per frame — which requires the resolution it was meant to replace.

## Specificity: already decided, and the decision holds

Arbitrary boolean guards make *"is A tighter than B"* entailment between predicates, which is not
computable in general. This is the standard objection to predicate dispatch and it does not need
re-deciding here, because `precedence._covers` already answers it and says why:

> Undecidable comparisons answer *no*, and the direction is `types.subsumes`' and taken for its reason: a
> false negative loses an ordering the author could have had, a false positive claims a precedence the
> author never wrote. **Losing an ordering is recoverable; an invented one is not.**

So specificity stays **syntactic and partial** — `_at_least_as_tight` knows two real refinements (a
subtype where a supertype would do; a direct link where a transitive one would do) and treats everything
else as equality. Two applicable bodies with incomparable guards fall through to the next stage of the
ladder, and the ladder ends total.

The consequence to state plainly: **incomparable guards are an author's problem, not the system's.** The
system will pick one and be able to say why (`governing` already reports which line stopped which rule);
it will not pretend one is more specific than the other.

## Self-sustaining constraints, and the two answers this engine already gives

The hardest question, and the one that decides how far this goes.

A guard reads the neighbours. A neighbour's type may itself be decided by a guard that reads *its*
neighbours. Configurations therefore exist that **support each other and nothing else** — *x is a
`container` if something is in it; y is `contained` if it is in a container* — and no per-node check can
settle them, because each is only true given the other. The interpretation is correct only if the whole
mutually-supporting assignment is globally consistent.

This engine has met that question twice and answered it **differently each time**, which is worth naming
before adding a third site.

* **`types._target_ok` is coinductive.** In its own words: *"A cycle in the data is satisfied, not failed.
  A `person` whose `friend` must be a `person` is a perfectly ordinary declaration, and two people who are
  friends make the check re-enter. The coinductive answer — assume it holds while proving it holds — is
  the only one that terminates without banning recursive types outright, and it is what every structural
  type system does."* That is a **greatest** fixed point: self-support counts as support.
* **The units-era work went the other way.** Stratification, demand-driven negation, and an ATMS
  experiment across forks that produced an **unsound false positive and was reverted**. There the stance
  was that a conclusion resting on itself is not a conclusion.

Both stances are defensible and they contradict. Type membership takes the generous reading; derivation
takes the strict one. Nobody has had to reconcile them because they never met — and predicate dispatch is
exactly where they would.

**The recommendation, and it keeps the contradiction rather than resolving it.**

1. **Dispatch stays bounded and coinductive.** Choosing a body is a decision at *one call site* over a
   *closed* candidate set — the bodies sharing that name. `types.py`'s founding claim is that it
   *"validates one argument at one call site, bounded and terminating, instead of deciding what fires
   across the whole graph"*, and the north-star repoint was **content as data, not matching as the
   execution model**. Predicate dispatch scoped to a call keeps both. Predicate dispatch that scans for
   applicable bodies is a production system by another name, and this project has already walked away
   from that once.

2. **A globally self-sustaining interpretation is not dispatch. It is a hypothesis.** When the assignment
   only holds as a whole, the thing being asked is *"is there a consistent reading?"* — and `hypothesis.py`
   is the mechanism, already built and already the right shape: a hypothesis is a node, **two rivals
   coexist as two nodes** rather than needing re-runs, the verdict is a fact a rule can read, and
   `workbench.step` already records a chosen assumption so `fragile_steps` can say which parts of a plan
   rest on guesses. *Assume the mutually-supporting reading, run it, see whether it closes* is what a
   workbench is for.

That split keeps the hot path cheap and puts the expensive answer where somebody asked for it. It also
means the honest statement of the limit is: **per call, dispatch answers with what is locally derivable
and treats a cycle as satisfied; a reading that is only true globally has to be proposed as a hypothesis
and checked, and the system will not find one for you.** Whether it *should* find one — a search over
consistent readings — is a real question and it is out of scope here, because it is a planning question
about interpretations and not a dispatch mechanism. It should be decided on its own terms, the way *may a
plan act on something it invented* was.

⚠ One concrete trap for whoever builds slice 2: the coinductive `_seen` set in `types.fails` is keyed by
`(node, type)`. A guard is not a type, so a guard that re-enters would need its own key — and a guard
whose evaluation dispatches is exactly how that happens. **A termination guard is tested by a query that
FAILS**, which is how `path.reaches` got its seen-set, so the check for this must be a world where the
mutual support does *not* close.

## What must not happen

* **The closed eight stay total and stay type-free.** `slot_of`, `set_slot`, `related`, `relations`,
  `relation_at`, `relate`, `unrelate`, `make` must resolve for every call. Dispatch that can fail to
  select is fine for an open class and fatal for a closed one — that is the whole argument for the middle
  layer in [mediated-access.md](mediated-access.md).
* **No scanning.** Candidates are the bodies sharing a name, found through the function index. Not
  "every function whose guard happens to hold".
* **The cheap gate first.** `types.is_a` is already on the hot path of every proposal, and
  `criterion._expand` warns that nested draws multiply — *"the one place a criterion's cost is not bounded
  by the goal"*. Parameter types are the prefilter; the guard is evaluated only for candidates that
  survive it.

## Build order

**Slice 1 — the two-place condition, no new dispatch. ✅ BUILT.** A function carries criterion-shaped
conditions over its *parameters* (`function.guard`), evaluated beside the parameter-type check.
`invoke` refuses with `GuardViolation` naming the condition that failed; `fn.applies` / `fn.unmet_guards`
answer for the planner, which filters on them in `enumerate_frame` and `check_call`. One name still means
one body, so no static reader changed and nothing became ambiguous.

✅ **And the surface is built**, as `when` / `unless` lines above the body:

```
fn stack(b: clear_block, onto: clear_block) -> block:
    unless b is onto
    INVOKE R(was) related node=F(b) label="on"
```

Lines rather than a header clause, for the reason a criterion uses lines: each condition is its own node,
so a refusal can say *which* one failed, and several fit. Only above the instructions — a condition
decides whether the body applies at all, so one written halfway down would read as though it applied from
there. `intake.condition` is **called, not copied**: the condition grammar belongs to `intake`, and a
guard's names are its parameters where a criterion's are roles, which the language cannot tell apart.
Guards round-trip through `unparse`, rendered from the stored test rather than from the text they were
written as.

**Slice 2 — several bodies, one name. ✅ BUILT.** `function.bodies` / `function.select`: candidates are
the bodies sharing a name, filtered by their guards, ordered most-specific-first by `precedence._covers`
with **declaration order** breaking every tie the partial order cannot. `invoke` selects before it loads,
so the body a call runs is the body the world chose. `driver.establishes` **unions** over the bodies —
an over-approximation, which is the direction that reader is contractually safe in.

Three constraints that fell out of building it:

* **Bodies sharing a name must take the same parameters.** A caller binds arguments before a body is
  chosen, so anything else is not dispatchable. Refused in `define`, where the author is, rather than at
  the call, where the message would name a function nobody wrote.
* **Selection happens on every call, not only when several bodies exist.** Which body a name means *is*
  what the call means; making it conditional would make the single-body case a different mechanism. It
  costs one edge read.
* **Nothing applicable is a refusal, not a fallback.** `GuardViolation` reports every candidate's reason,
  because *why did none of them mean this* is a question about the set.

**Slice 3 — the situation in a guard.** Conditions that speak of the ambient goal, reached by walking the
chain. This is what makes *go to the bank* work when the world cannot decide it.

**Slice 4 — `wants_that_unblock` reads guards.** The prize: a failed guard becomes a subgoal.

Slices 1 and 2 are separable and slice 1 is worth doing whatever happens to the rest.

## Open questions

1. **Where does the guard live — on the function, or beside it?** A `criterion` is already a node with
   tests and precedence. A function's guard could *be* a criterion node, which buys `governing` (*which
   line ruled this body out*) for free and makes one condition mechanism serve both. The risk is
   conflating two things that are genuinely different: a criterion says *what to do*, a guard says *what
   this name means here*. Sharing the node kind is what `consequent.py` already does across families for
   the opposite reason.

2. **Does a guard participate in `applicable` for mocks?** A mock's condition is its parameter types
   today. If guards exist, a mock should presumably get one — and then conditioned mocks and dispatched
   bodies are the same mechanism, which is either an elegance or a conflation.

3. **What does a guard see — the arguments, or the frame?** Under the identity model a rule is bound to
   the real node and the frame decides what a read means. A guard must therefore evaluate through the
   view (`workbench.View`, `path.adjacent`), or it will read reality while the body it guards reads the
   frame. That is the same defect `function.invoke`'s type check had until this arc, and it is written
   down as a trap in [HANDOFF.md](HANDOFF.md).

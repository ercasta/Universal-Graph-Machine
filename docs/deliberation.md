# Deliberation

Because nothing fires, something must decide what to do next, and that decision is the whole of the
system's control flow. Deliberation is where authored knowledge enters: what a domain expert knows
about which move to make, which route is sanctioned, and what may never be done.

Everything on this page is **data**. The engine ships the readers, rankers and matchers; a domain
contributes nodes, written in the [controlled language](authoring.md). That division is deliberate:
two programs cannot be compared for disagreement, a parser cannot refuse a bad one, and a reader
cannot inspect one.

## The decision point

At each search step the machine chooses one of a closed set of verbs. Small and closed on purpose —
this is the vocabulary everything authored has to speak.

| verb | meaning | who supplies it |
|---|---|---|
| `EXPAND` | imagine the best-ranked proposal — the default behaviour | the engine |
| `DECOMPOSE` | post subgoals instead of enumerating actions | a method or procedure |
| `COMMIT` | stop planning; execute what we have | a stop rule |
| `SENSE` | stop planning and act **in order to learn** | a stop rule, on an unknown |
| `REFUSE` | there is no sanctioned way to proceed; do not improvise | a procedure that does not fit |

`SENSE` is distinct from `COMMIT` even though both stop planning and act, because the *reason*
differs and the reason is what a later reader needs. `REFUSE` is distinct from "no plan found" for
the same reason: one is an absence, the other is a prohibition.

## Four forces, distinguished by what happens when they do not fit

This is the distinction that matters most, and it is not about strength — it is about **failure**.
Two authored decompositions can look identical and behave oppositely.

| kind | force | when it does not fit or does not work |
|---|---|---|
| constraint (`never`, `at most`) | hard | **prune** — a breach proves every extension is dead |
| procedure | mandatory | **refuse** — do not improvise |
| method | advisory | **fall back to search** |
| guideline (`prefer`, `avoid`) | soft | **reorder only** — never prunes, never fails |

Because force cannot be inferred from content, the surface makes the author say the word. `method`
and `procedure` accept the same body; so do `criterion` and `directive`.

**Why a procedure is not a method.** As an efficiency device, a decomposition that does not cover a
case should fall back to search — incompleteness is fine. As a *compliance* device it must not:
finding another route is precisely the forbidden act. For a procedure, "no plan found" is a better
outcome than "found a plan another way". That reverses the engine's every other reflex —
`carry_out` replans, `recover` tries contingencies, `pursue` keeps searching — so the reflex has to
be suppressible, deliberately and visibly.

**Three justifications for narrowing a search, and they must not be confused.**

* A constraint prunes on a **proof**: no continuation of a plan that used a forbidden action makes it
  unused.
* A guideline reorders on a **guess**: it is an author's opinion about what will help, and excluding
  on it could lose a solution. Sussman's anomaly is the standing counter-example — the winning move
  scores low.
* A method prunes on **authority**: it is not a guess about what will help but an author's
  commitment about what the sanctioned decomposition *is*. This is also where the exponential win
  lives, because a method *replaces* enumeration rather than ordering it, which is why it cannot be
  expressed as a ranker.

## Guidelines — advice that can be wrong without being unsound

The weakest force, and the only one that can never change what is reachable.

```cnl
prefer washing first:
    action wash
    touching c
    when clear_block
    because it is cheaper
```

A guideline names an operator, an individual it must bind, or a type its subject must satisfy, and
adjusts order within what relevance already decided. `avoid` means *later*, not *never*: only
`never` in a goal means never, and only it prunes. Conflating the two is how advice quietly becomes
a correctness rule and hides the one move that worked.

Guidelines order *within* a relevance band and never across one. Relevance is derived from structure
— it reads the function's stored body — while a guideline is a heuristic, and letting weaker
evidence beat stronger is how an authored preference makes the system worse than it was.

Advice naming neither an action nor a thing is refused: it would match everything, and that is not
advice.

## Methods and procedures — authored decomposition

A method says: for a goal of this shape, in this context, raise these subgoals in this order. It
selects itself — an author never assembles subgoals by hand.

```cnl
method service then wash:
    handles type washed_car
    when car
    because a car is washed after service
    some w in subject by wheel
    step subject is a serviced_car
    step subject.clean = true
    step w.clean = true
    step subject on object
```

Steps speak of **roles**, never names — `subject` and `object`, meaning the matched constraint's. A
method naming an individual would be about that individual and could not be reused. Where a step
needs to reach a third individual the constraint never names, `some … in … by …` binds one by
traversal.

That binder deliberately binds **one** thing, the nearest. A traversal reaches a set, and raising one
subgoal per member produces a plan valid only for the collection as it stood when the plan was made.
For *do it to each of them*, write the universal as a type and let the goal's witnesses drive it one
member at a time.

Goals form a hierarchy, so a method's subgoals are ordinary goals with a parent, a reason for being
raised, and queryable ancestry. Context comes from that ancestry, and never from a rule's name: "in
the context of goal z, do this" must not be encoded by writing a rule that only exists at that
position, because the ancestry already entails the context and asserting it twice gives it somewhere
to drift.

## Criteria and directives — expert judgement

The engine's own guidance is domain-blind: relevance scores a proposal by whether it writes an open
constraint, so a move that unblocks without closing anything scores zero. A criterion is authored
knowledge that names the move outright.

The difference is not a constant factor. With criteria the search imagines **five states whatever
the size of the world**, where relevance goes from 139 states to 357 and then stops finding a plan at
all between six and seven blocks.

```cnl
criterion clear the block that must move:
    wants link on
    some top in subject by ^on
    when top is a clear_block
    unless wants link on from object
    do unstack b = top, floor = the ground
    because nothing can be stacked while something sits on it
```

A criterion is an ordered list. Each takes the goal and the context and returns either an action — a
function with its arguments — or nothing. The first that speaks wins, precedence being declaration
order. That is the same choice guidelines make and for the same reason: weights are the thing that
needs tuning, and there is nothing to tune in an order.

`wants` is where the variables come from. It matches an **unmet** constraint of the goal and binds
`subject` and `object` from it. A criterion may not name individuals, so without it there is nothing
to speak about — and it is also exactly what an index would key on.

Conditions each occupy their own line, so a reader can be told *which one* ruled a candidate out.
That matters more than it looks: "why did this not happen?" is a requirement rather than a bonus, and
`criterion.governing` answers it by naming the condition that failed.

A criterion that cannot act in a situation is **silent by design** — the first container happening to
be the one this goal forbids is a *situation*, not a mistake. But a criterion naming a function that
does not exist is wrong in every world, so a `do` line is checked against the function library where
it is written: the function must exist and the arguments must bind every parameter and no others.
Folding a typo into the same silence made a mistake look exactly like judgement that did not apply.

### Force, again

| | suppresses enumeration | when it cannot act |
|---|---|---|
| `criterion` | **defers** it — being wrong costs imagined states | falls silent; the search carries on |
| `directive` | does **not** defer — the alternatives are never built | **refuses** |

A directive with no conditions recognises *every* matching unmet constraint and refuses in all of
them, becoming a blanket veto over everything declared after it. Mandatory force obliges the author
to say what to do in every case they claimed to govern; that is the price of removing the fallback.

### Criteria that disagree

Two criteria speaking about the same situation and naming different actions is a real disagreement,
and it can be reported: which one won, which lost, and what each would have done. A criterion that
merely agrees is not reported, and a criterion that stays silent is not a conflict.

## Norms — prohibitions that can be defeated

`never` prunes absolutely, which is right for a law and wrong for a defeasible default. A domain may
hold standing house norms of differing strength (*don't sell* as a default stance, *never
counterfeit* as inviolable), transient instructions (*today it is good to sell*), and an authority
ranking among them (*today outranks standing*, and nothing outranks the law).

A norm is that, as data: a prohibition or permission about an action, attributed to a source, with
an authority ordering that arbitrates between them. Settling an action asks which norms speak about
it and which of those outranks the rest; when nothing decides, the answer is *undecidable* rather
than a silent default.

## Conflict

The concern this addresses is old, but the old notion does not transfer, and copying it would have
been wrong. A rule engine deriving facts can say that two rules concluding contradictory things is a
contradiction, full stop. This engine performs actions in sequence, and a later action overriding an
earlier one is not a disagreement — it is what doing things looks like. `stack` sets one block
unclear and another clear every time it runs; reporting that as a conflict would bury the real ones.

What survives is **interference**: two independently authored functions, composed by a library that
grew without either author knowing about the other, writing the same slot **for different goals**.
The qualifier is what makes the detector useful rather than noisy — the same two writes serving one
goal are a deliberate sequel.

Conflicts are also detectable *before* anything runs. Two plans that have both been found but neither
executed can be compared for the slots they intend to write and the values they intend to write
there.

Contradictory goals are a separate check: a goal wanting two incompatible values on one slot is
unsatisfiable, and saying so is better than searching until the budget runs out.

## Rates, and where the cost goes

Each kind must be consulted at its own rate, or the cure costs more than the disease. A search
routinely reaches hundreds of imagined states and enumerates thousands of proposals.

| kind | consulted | frequency | so it must be |
|---|---|---|---|
| method, procedure | when a goal is opened or attempted | few | may be expensive |
| stop rules (`COMMIT`, `SENSE`, `REFUSE`) | per search step | hundreds | cheap and structural |
| guideline | per proposal, inside ranking | thousands | a pure ranker |

Any per-step decision whose answer depends only on the goal should be computed once per goal. The
engine's own largest measured speed-up came from hoisting loop-invariant work out of enumeration, not
from making the inner test smarter.

## Precedence

When several apply, in this fixed order:

1. a constraint breach — prune (proof)
2. a procedure applies — decompose, or refuse if it cannot be followed (mandatory authority)
3. a method applies — decompose (advisory authority)
4. a stop rule fires — commit or sense
5. otherwise — expand, ordered by relevance, ties broken by guidelines

No weights and no scores to tune. Where several of one kind apply, declaration order is precedence.
Introducing a numeric combiner would introduce tuning, and tuning is the cost this project
consistently declines to pay.

## Ignorance, and knowing to go and look

A goal can bottom out in something the machine simply does not know. That is a third search outcome
alongside success and failure, and it is what `SENSE` exists for: stop planning, act in order to
learn, then carry on. It fires only when the goal genuinely bottoms out in ignorance rather than
merely touching it.

The counterpart is **volatility** — how often a slot has been observed to change, and how often it
changed without the agent having been the cause. A slot that moves under the agent scores high and is
worth looking at again; a slot only the agent touches scores zero. That gives sensing something to
aim at rather than a fixed policy. See [Memory and time](memory.md).

## Judging its own computation

Because the search's state is graph data and the loop yields between primitive steps, a rule written
as ordinary text can watch a computation that is currently running and stop it — *am I taking too
long over this? If so, stop planning* — reporting in its own words why it stopped, with the world
untouched and the pursuit giving up honestly. Monitoring and control are separable, and both are
authored rather than built in.

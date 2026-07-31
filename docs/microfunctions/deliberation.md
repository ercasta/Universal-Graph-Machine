# Deliberation — deciding what to do next, and following authored knowledge

> **Slice 1 is BUILT (2026-07-31).** `driver.pursue` takes a `decide` hook, the five verbs exist, and
> `check_the_deliberation_seam_is_inert_by_default_and_live_when_used` holds it. 135 checks, 0 FAILED; the
> default path is identical and the search is still deterministic. §11 records what that slice did and did
> not do. Everything else below remains designed-only.

> **⭐⭐ STANDING PRINCIPLE, stated 2026-07-31: MICROFUNCTIONS SHIP WITH THE ENGINE.** They are *how the
> engine works*, not a user-definable thing — nobody should need to touch or extend them. Everything a
> domain contributes is **data**: goals, decision rules, procedures, guidelines. This is what makes §10's
> "decision rules are data, not microfunctions" the general rule rather than a special case, and it
> collapses the four-surfaces worry: `asm.py` is then an *internal* authoring convenience and there is one
> external surface, which is data that can be refused. ⚠ It also **narrows the LLM border further, in the
> safe direction**: a model writes data a parser can refuse, never a program nobody can check.
> ⚠ It is in tension with things currently written down — see §11.

**Status: §§0-10 are DESIGNED ONLY, and nothing in it is measured.** Every quantitative claim
in `HANDOFF.md` came from a probe; there is no probe behind this document yet, and the recent history of
this project is that measurement makes claims *weaker*. Read the numbers-free parts as proposals and the
hazards as the load-bearing content.

Written 2026-07-31, out of a design conversation following the enumeration-cost work (`HANDOFF.md` §5m).

---

## 0. The one architectural change

Everything below is a consequence of a single change, and it is worth stating alone because the rest is
downstream:

> **`driver.pursue` is a closed loop with no yield point.** It runs to success, failure, or budget. Nothing
> can intervene between two imagined steps, so no decision about *what to do next* is expressible.

`pursue` and `carry_out` are Python functions invoked from outside. They are never microfunctions, never
registered tools, never reachable from the ISA — checked. So **deliberation is the thing the system
computes with and cannot compute about.**

⭐ **This is the same defect in its third incarnation, and the project has fixed it twice already.**
`Focus` was a Python object holding no graph state, so attention could not be looked at — fixed by
`thread.py`. `want` was a Python string, so the goal could not be pointed at — fixed by `goal.py`, whose
docstring calls it "the same defect attention had before `thread.py`, in a different place." This is the
third place. `metaprocedure_model.md` also already records that moving a mechanism which derives
*reasoned-over state* into Python was itself a mistake, and "which proposal to expand next" is exactly
reasoned-over state.

The change: **the search loop consults a decision at each step, and the decision is data.** Guidelines,
methods, procedures and stop-and-act then stop being four features and become four *kinds of decision*.

## 1. Five verbs

The decision point returns one of a closed set. Small and closed on purpose — this is the vocabulary
everything authored has to speak.

| verb | meaning | who supplies it |
|---|---|---|
| `EXPAND` | imagine the best-ranked proposal — **today's entire behaviour** | the default |
| `DECOMPOSE` | post subgoals instead of enumerating actions | a method or procedure |
| `COMMIT` | stop planning; execute what we have | a stop-rule |
| `SENSE` | stop planning and act **in order to learn** | a stop-rule, on an unknown |
| `REFUSE` | no sanctioned way to proceed; do not improvise | a procedure that does not fit |

`SENSE` is deliberately distinct from `COMMIT` even though both stop planning and act, because the
*reason* differs and the reason is what a later reader needs. `REFUSE` is distinct from "no plan found"
for the same reason: one is an absence, the other is a prohibition.

## 2. Two prerequisites, both structural

### 2a. The search must be steppable

Factor `pursue`'s `while` loop so a single step can be taken and a decision consulted between steps.

⚠ **This has been designed once already.** `docs/design/procedures_design.md` §3 is a *stepping bank*,
built and green in the old engine (Slice 1, 2026-07-16). The code is gone; the findings are not. Read it
before re-deriving. Expect the same outcome as conflict detection (`HANDOFF.md` §5j): **the findings
transfer, the mechanism probably does not.**

### 2b. Goals must have hierarchy

Checked: `goal.py` has **no subgoal relation** — no parent, no child, no stack — and `intake.py` is the
only caller of `open_goal`. So `DECOMPOSE` has nothing to post and no context to key on.

Needed: a `subgoal` edge, ancestry queryable by a microfunction, and goals mintable *from* a microfunction
rather than only from intake.

⚠ **Do not let authors encode context by unrolling it into nested rules.** "Given goal z, if within
subgoal y then…" can always be rewritten as a rule that only exists at that position — and that is a
**labelling error**, the pattern this project has recorded twice (the `in_workbench` marker, the `is_a`
stamp): the goal ancestry *already entails* the context, so asserting it a second time in the rule's
identity gives it somewhere to drift. It also forces one rule per position it could occupy, which is the
duplication `../pystrider` hit across two `.mf` files. **Make ancestry queryable; do not make context part
of a rule's name.**

⚠ Prior art here too: `docs/units/goal_machinery.md` §8 — *"Built and run, 2026-07-29 — a subgoal with its
own condition"* — plus findings on interning guards and additive rewriting.

## 3. Four forces, distinguished by what happens when they DON'T fit

⭐⭐ **This is the distinction that matters most, and it is not about strength — it is about failure.** Two
authored decompositions can look identical and behave oppositely.

| kind | force | when it does not fit / does not work |
|---|---|---|
| **constraint** (`forbid_action`) | hard | **prune** — a breach is a proof every extension is dead (§5e) |
| **procedure** | mandatory | **REFUSE** — do not improvise |
| **method** | advisory | **fall back to search** |
| **guideline** | soft | **reorder only** — never prunes, never fails |

**Why procedure ≠ method, and why it inverts this engine's disposition.** As an efficiency device, a
decomposition that does not cover a case should fall back to search — incompleteness is fine. As a
*compliance* device it must not: finding another route is precisely the forbidden act. So for a procedure,
**"no plan found" is a better outcome than "found a plan another way."**

That reverses every existing reflex — `carry_out` replans, `recover` tries contingencies, `pursue` keeps
searching. The reflex has to be suppressible, deliberately and visibly. ⚠ **The force cannot be inferred
from the content and must be declared.**

**Why a guideline cannot prune.** §5d's Sussman check exists because the winning move scored *low*.
Guidelines are guesses; the standing rule is **rank a guess, prune a proof**. A guideline that excluded
its tail would lose exactly the cases the check was written to protect.

**Why a method may prune where a guideline may not.** A method is not a guess about what will help, it is
an author's *commitment* about what the sanctioned decomposition is. It prunes on **authority**, not on
evidence — a third justification alongside proof and guess, and it must be named as such rather than
smuggled in as a strong heuristic. ⭐ This is also where the exponential win lives: a method *replaces*
enumeration (6,480 proposals → one decomposition), which is why it cannot be expressed as a ranker.

## 4. Frequency — the thing most likely to be got wrong

⚠ **Each kind must be consulted at its own rate, or the cure costs more than the disease.** Deliberation
that runs per imagined step inverts the cost of the thing it optimises. Today's search reaches ~400
imagined states routinely and enumerates thousands of proposals.

| kind | consulted | rate | so it must be |
|---|---|---|---|
| method / procedure | when a goal is opened or attempted | few | may be expensive |
| stop-rules (`COMMIT`/`SENSE`/`REFUSE`) | per search step | hundreds | cheap, structural |
| guideline | per proposal, inside ranking | thousands | a pure ranker — the existing `rank=` hook |

⭐ Note the third row needs **no new mechanism at all**: `pursue(rank=...)` already exists and is
documented for exactly this ("a learned policy, a language model reading `function.catalogue`"). Guidelines
are therefore the cheapest slice and are independent of everything else here.

**And the lesson from `HANDOFF.md` §5m applies in advance:** the enumeration win came from *hoisting
loop-invariant work out*, not from making the inner test smarter. Any per-step decision whose answer
depends only on the goal should be computed once per goal, not once per step.

## 5. Precedence — fixed, declared, no weights

When several apply, in this order:

1. **constraint breach** → prune (proof)
2. **procedure applies** → `DECOMPOSE`, or `REFUSE` if it cannot be followed (authority, mandatory)
3. **method applies** → `DECOMPOSE` (authority, advisory)
4. **stop-rule fires** → `COMMIT` / `SENSE`
5. **otherwise** → `EXPAND`, ordered by `relevance`, ties broken by guidelines

⚠ **No weights, no scores to tune.** Where several of one kind apply, use **declaration order as
precedence** — the precedent is `mock`, where "declaration order is preference order, free, because `mock`
is an ordered edge." Introducing a numeric combiner introduces tuning, and tuning is the cost this project
has consistently declined to pay.

⚠ **Guidelines must not overturn a band-4 `relevance` score** in the first version. Band 4 is *derived from
structure* (`establishes` reads the function body); a guideline is an author's heuristic. Letting the
weaker evidence beat the stronger is how an authored preference makes the system dumber than it was. The
tension is real — an author may genuinely know a band-4 move is a trap — but that should be argued by a
concrete case, not granted up front.

## 6. Hazards to design for, not discover

**⚠ Subgoals minted during search are metadata about the search.** A decision rule runs while imagining,
and what it posts is not part of the world. So (a) it must obey the direction invariant — pointed at, never
pointed *at by* world nodes, or every workbench copy becomes unbounded; and (b) it lands in the hazard
`types.instances` names in its own docstring, *"planning about the products of planning"*. Decide where a
subgoal minted at depth 4 lives **before** writing any of it.

**⚠ The visited key grows again.** §5e already changed it from `state` to `(state, outstanding)` because
two routes to the same world differ if one has done a required action. The goal stack is the same argument
a third time: two routes to the same world differ if one is inside a procedure and the other is not.
Deduping on the world alone would silently discard the compliant route — the same class of bug as §5c's
action-vs-state dedup, which reported a plausible "no plan found".

**⚠ Recursive methods cycle.** A rule posting a subgoal whose rule posts another is how repetition gets
expressed, and it is how the loop hangs. `max_depth` and the visited set are keyed on world *state*; a
goal-stack cycle where the state does not change is caught by neither.

**⚠ Sense–replan can cycle too.** Each iteration honestly justified, forever. `carry_out`'s `attempts=3` is
the only existing brake and it is crude.

**⚠ Authored preferences can now disagree with each other.** This is the feature-interaction problem
`function.py` already cites as prior art, and `conflict.interference_between` already reports a collision
between two plans before either runs. But it would be the first time *preferences* rather than *goals* can
conflict, and that should be visible from the start rather than surfacing as mysterious ranking behaviour.

## 7. Compliance needs auditing, and most of it already exists

Regulated use does not only require doing the right thing, it requires *demonstrating* it. This engine is
unusually well placed:

- the thread records what was **considered**, not only what **ran** (§5j's `done` marking) — so a report can
  show what was rejected;
- an application records which function was applied to which *subject*, with bindings;
- `fragile_steps` says which steps rested on assumptions;
- and `check_why_answers_from_history_and_never_invents_it` holds `AND_INVENTS_NO_DERIVATION` — the system
  distinguishes "I derived this" from "I was told this" and refuses to fabricate a justification.

What is missing is only the ability to say **"this run was governed by procedure P"** and have that be
checkable afterwards. Every decision should land on the thread with its reason; the thread already carries
a reason as an edge property on `prev`, so this is nearly free.

**⭐ And "I complied" is not "it worked".** A procedure can be mandatory *and* insufficient. §5g already
split `record_plan` ("I know how to do this") from `close_goal` ("this is now true") after the driver closed
a world goal on imagined evidence. This is that split one level up: in a regulated context the first claim
is often the one that matters legally and the second the one that matters practically. **Both must be
separately recordable, and neither inferable from the other.**

## 8. Ignorance, and why `SENSE` needs it

Today the engine performs information-gathering actions but **models them as world-changing ones**:
`scan_dir(d: dir) -> listing` has a mock that *mints file nodes*, as though scanning created files. That
fudge is why planning toward "some file exists" works (§5f), and it is also why the system cannot
distinguish **"make p true"** from **"find out whether p"**.

Underneath: there is no representation of ignorance. An attribute is present or absent, and `None` means
*lacks it*, never *unknown*. So an information-gathering subgoal has nothing to close.

⭐ **The fix rides on §5d's existing insight rather than needing new machinery.** That section's point was
that a goal answering only yes/no forces blind search, while one naming *which constraints are false* lets
the driver ask what could close them. Extend it one notch — let `unmet` distinguish **false** from
**unknown**:

- unmet-because-false → find an action that makes it true (today)
- unmet-because-unknown → find an action that resolves that slot → `SENSE`

`establishes` already reads effects off bodies *including mocks*, so it can already see which actions write
a given slot. No new planner; one new reason a constraint is unmet.

⚠ **A mock must keep its second job.** Mocks are both (a) what gets substituted when imagining and (b)
where `establishes` learns that an opaque `DISPATCH` can do anything at all. `SENSE` means *decline to
substitute*, never *ignore the mock* — conflate them and declining an assumption makes the action invisible
to planning, which is the opposite of planning toward finding out.

⚠ **You cannot imagine past a genuine unknown**, so a plan reaching one is complete in the only sense
available. The criterion for `SENSE` should be that the plan **bottoms out** in ignorance — every remaining
unmet constraint is unmet-because-unknown and the last step resolves one — not merely that it *touches* an
unknown, which would make the system sense promiscuously.

**A structural criterion for when to assume versus sense.** §5 item 4 says branch only where being wrong is
expensive, without saying how to tell. Proposal: **the cost of a wrong assumption is bounded by what you
will have done before you discover it.** If everything downstream is imagining, being wrong costs nothing —
execution diverges and the loop replans. If a **dispatch** falls downstream, being wrong costs a real,
possibly irreversible act. And that is checkable statically, because `dispatch.py` is deliberately the one
choke point every effect leaves through.

> **Assume freely before the first irreversible act. Branch or sense where an assumption is load-bearing
> for one.**

## 9. Order of work

1. ~~**Steppable search + an inert decision point.**~~ **DONE — §11.** `decide()` always returns `EXPAND`. ⭐ **Zero behaviour
   change, verified by the existing 134 checks and by the search staying deterministic.** Land the seam
   before anything stands on it — this is the project's idiom and it makes every later slice a small diff.
2. **Guidelines.** Independent of everything else and nearly free — a ranker through the existing `rank=`
   hook. Earliest real value, and it exercises "authored knowledge that can be wrong without being unsound".
3. **Goal hierarchy.** The `subgoal` edge, ancestry queryable, goals mintable from a microfunction. Read
   `goal_machinery.md` §8 first.
4. **Methods** (`DECOMPOSE`, advisory). ⚠ With a check that a goal solvable by search **stays solvable**
   when a method that does not cover it is added — that property is easy to lose silently.
5. **Procedures** (mandatory, `REFUSE`) + the audit recording of §7. ⚠ With the *opposite* check: adding a
   procedure must make an off-procedure route refuse, and the refusal must name what governed it.
6. **Ignorance and `SENSE`** (§8). Largest, and the only one needing a substrate change.

## 10. Open questions, stated rather than buried

- ~~**Is a decision rule a microfunction, or a new node kind?**~~ **DECIDED 2026-07-31: DATA, not a
  microfunction.** The tempting answer was a function that reads state and mints goals — homoiconic for
  free, readable by `establishes`, no new mechanism. It was rejected because it makes the condition a
  **program** rather than a **pattern**, and three things need patterns: `conflict.py` cannot say two rules
  disagree by comparing two programs (halting, not matching); a CNL surface can parse a pattern and refuse
  a bad one, where it could only ever emit a program it cannot check; and a program's condition is not
  *disputable* by a reader, which is the property §7 needs for compliance. ⚠ The cost is that a condition
  now needs its own vocabulary rather than borrowing the ISA — see the next question, which this promotes
  from a detail to a prerequisite.
- **What is a condition written in?** `types.py` is a checkable subgraph schema and its docstring says
  matching lives there and only there — but schemas are one level deep and cannot relate two parameters
  (§5c). Goal constraints have the three sorts that reach further. Probably: a condition takes the same
  three sorts a goal's constraints take, plus goal-ancestry queries. Unverified.
- **One CNL or four?** That would be four surfaces — functions (`asm.py`), goals (`intake.py`), guidelines,
  decision rules. A decision rule mentions goals *and* actions *and* conditions, so it needs vocabulary from
  both existing parsers. Converging them risks a big-bang rewrite; not converging them risks the exact
  vocabulary drift `../pystrider` had to hand-roll a check for.
- **Does `COMMIT` ever fire without a stop-rule?** i.e. is there a structural "this plan is good enough"
  that needs no authoring? Budget exhaustion already yields an honest `UNKNOWN` (precedent: the book
  chapter's `max_rounds`). Whether anything else qualifies is unknown.
- **Termination for recursive methods and sense–replan cycles.** Named in §6, unsolved. The engine's
  recorded position is that "termination and conflict arbitration are both open"; this makes the first one
  sharper without answering it.

---

## 11. Slice 1, as built (2026-07-31)

`driver.pursue(..., decide=...)`, consulted once per imagined step, **before** the chosen proposal is
imagined. Returns `None`/`EXPAND` for "nothing to say" — so **the default is to keep planning** and a
decision has to speak up to alter it — or `verb`, or `(verb, reason)`.

**What makes it inert.** The only change on the default path is that `steps += 1` moved below a block that
is skipped when `decide is None`. Nothing is recorded unless a decision actually fires. Verified two ways:
the existing 135 checks, and the search still returning identical results across repeated runs in one
process (`HANDOFF.md` §5l's property, which is the one a subtle reordering would break).

**⚠ The vacuity guard is the whole test.** A seam nothing can steer is indistinguishable from no seam, and
would pass any check asserting only "default behaviour is unchanged". So the check requires **both**: the
default path identical, *and* a decision actually diverting the search. Planted-bug probe per `HANDOFF.md`
§7: a `pursue` that consults `decide` and discards the answer fails the check.

**⚠ `decide` is a participant, so it gets the real thing.** `trace` receives labels because a watcher must
not be able to steer and a rendering is all it needs; a decision is made *on structure*, so renderings
would force it to reconstruct state from strings. Same reasoning, opposite conclusion, and the two must not
be made to look alike.

**⚠ Built from what is already computed.** `open_count` rides on the frontier item precisely so nothing is
recomputed per step. This runs hundreds of times in a normal search, and §4's rule is that anything costly
here inverts the cost of what it exists to save.

**Unbuilt verbs raise, they are not ignored.** `DECOMPOSE` names the missing goal hierarchy and `SENSE`
names the missing representation of ignorance; an unrecognised verb raises too. A decision that silently
does nothing is the failure this project keeps catching.

**⚠ What slice 1 did NOT do, stated so nobody assumes it.** The search is not *externally* steppable — there
is no resumable generator, no way to stop and continue later. What exists is a decision point *inside* the
loop, which is what every §3 force needs; full externalisation is a separate question and
`procedures_design.md` §3's stepping bank is the prior art for it. `COMMIT` and `SENSE` currently *stop*
and hand back the prefix (`plan`, `frame`); nothing yet executes that prefix, which is `carry_out`'s job
and a later slice.

## 12. Where the "microfunctions ship with the engine" principle lands

It resolves §10's first open question by generalising it, and it improves the design in three places: one
external surface instead of four, a tighter LLM border, and `establishes` becomes the engine reading *its
own* operations rather than reading user code.

**⚠ But it is in tension with what is currently written and currently practised**, and pretending otherwise
would be the drift this project keeps catching:

- `north_star.md`'s repoint is literally "rules become **microfunctions**", and `function.py`'s headline is
  "**a rule is a function**".
- `asm.py` is documented as "the text surface and **LLM border**" — i.e. exactly where a model writes.
- `../pystrider`, the first consumer, authors `.mf` files (`strider/rules/*.mf`), and `HANDOFF.md` §5k
  added the `INVOKE` surface **specifically so they could compose microfunctions in authored text**. Under
  this principle that feature served a use case that should not exist.
- `application.compile_episode` *learns* microfunctions — the system extending the engine, which the
  principle forbids.

**The unsettled question, which decides how much of the above has to change: where do DOMAIN ACTIONS sit?**
`stack`, `service`, `scan_dir` are domain-specific and are microfunctions today.

The reading that seems coherent: microfunctions are the **operation layer** — primitives and tool bindings,
shipped by the engine or by whoever integrates it — while everything constituting *knowledge* (what to
want, what to prefer, which procedure governs, what decomposes into what) is data. Under that reading
`stack` is an operation and "the approved procedure for X" is data, and the line is drawn at *knowledge
versus capability* rather than at *who typed it*.

⭐ **And it sharpens the learning story rather than damaging it.** If the system may not write operations,
then learning must produce **methods and procedures — data — not new code.** That is exactly where the
design conversation had already arrived from the other direction: a learned chunk is a *decomposition*,
which is a method, which is data. `compile_episode`'s current shape (learning a microfunction) is the thing
that would have to change, and the EBL argument says it should anyway.

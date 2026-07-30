# The graph data model — meta-concepts, operations, and the closure that buys unbounded depth

**Status: design, 2026-07-30. Written directly after `planning_meta_concepts_arc.md` §12, which ends by
saying the closed executable core is small and everything else is "open content read by a comparatively
small number of generic meta-rules, all sharing one representational shape." That sentence names a shape
without ever writing it down. This document writes it down.** Read `metaprocedure_model.md` §1a/§1b first
for the VM/content and privilege split this depends on, and `goal_machinery.md` §1 for the one table this
generalizes.

**The framing this exists to serve, stated by the user and worth keeping verbatim:** *the system does not
run algorithms — it is goal-driven, and computes by choosing and applying one metarule at a time. Its
effectiveness is therefore determined by how well it chooses the next metarule, not greedily only, but
knowing that specific subsequences work particularly well ("learned metaprocedures"). So the missing piece
is a good graph data model: how a goal, a plan, a hypothesis are represented, and precisely what operations
we perform on them.*

That framing is correct, and it has a consequence the rest of this document is mostly about: **if selection
quality is what determines effectiveness, then the thing being selected among has to be a graph citizen.**
A metarule application that exists only as "the Python driver happened to call `revive()` and this rule
matched" cannot be preferred, ranked, recorded, or compiled into a learned subsequence, because there is
nothing there to point at. §6 is the gap that follows from this, and it is the one real hole this
formalization found.

---

## 1. Two loops, and which one this document is about

Nothing here changes `metaprocedure_model.md` §1a's split. There are two loops and they are different in
kind:

- **The inner loop is fixed and is not a choice.** Match a pattern, fire an effect, propagate, settle. This
  is the closed algebra — conjunctive matching, θ-gated NAF, band meet, five substrate effects — and modus
  ponens is *this*, not a metarule over it (`planning_meta_concepts_arc.md` §9). A KB author does not
  change it, and nothing in this document proposes to.
- **The outer loop is the choice.** Which metarule to apply next, on which goal, with what focus, and
  whether to hypothesize before committing. This is what the user's framing calls the metarule sequence,
  and it is where "how well the system chooses" lives.

The confusion worth pre-empting: "the system does not run algorithms" is a claim about the **outer** loop
only. The inner loop absolutely is a fixed algorithm, and should be — that is `metaprocedure_model.md`
§1a's whole point about the CPU's fetch-decode-execute loop correctly not being a program the CPU runs.
What must not be a fixed algorithm is the *sequence of metarule applications*, because that is exactly
what the domain makes unpredictable (`planning_meta_concepts_arc.md` §4's red-light argument).

---

## 2. The representational discipline — four requirements, and why they are the ones

Before the concept-by-concept table, the general shape. A meta-concept is well-formed for this system when
it satisfies all four of these, and the fourth is the one that does the real work:

1. **It is a node with a kind marker**, not a Python object and not an attribute encoding. (`goal`,
   `<hypothesis>`, `<call>`.)
2. **Its parts are role edges to other nodes**, never structured values. (`wants`, `raised`, `pre`,
   `before`, `step`.) A role edge is matchable and walkable; a tuple packed into an attribute value is
   neither.
3. **Its lifecycle is a positive attribute**, concluded — never read off an absence. (`achieved`,
   `diverged`, `done`, `chosen`, `ready`, `discrepancy`.) `goal_machinery.md` §8's vacuous-achievement
   wrinkle is the standing evidence for why: an absence is trivially true before anything has been minted
   at all, so a lifecycle read off absence reports success before work begins.
4. **Every node it points at is drawn from this same table.** This is the closure requirement, and §5 is
   the argument that it — and only it — is what makes unbounded-depth composition a structural property
   rather than something to be tested by sampling.

A fifth requirement applies to the *lifecycle attributes specifically*, and is not representational but
about write access: per `metaprocedure_model.md` §3 Gap B, `chosen`/`ready`/`waits_for`/`done` are today
ordinary predicates any business rule can forge. The reserved-predicate registry proposed there is the
fix, and this document's table is exactly the list that registry needs to contain — which is a second
reason to write the table down.

---

## 3. The concepts, as they actually are in the graph

Two substrates carry these today: `ugm/` (the chosen foundation — CNL-authored, predicate-shaped) and
`units/` (the findings substrate — `atom`/`role`/`StandingUnit`). Per
`ugm-substrate-foundation-decision`, `ugm/` is where this lands; `units/` columns are given because that
is where several of these were actually *checked*, and losing the correspondence would lose the evidence.

| concept | node | parts (role edges) | lifecycle (positive attrs) | status |
|---|---|---|---|---|
| **goal** | `goal` | `wants -> claim` | `achieved` / `diverged` / `abandoned` | **built + checked**, `goal_experiment.py` |
| **subgoal lineage** | (reuses `goal`) | `raised -> goal`, interned per parent+condition | inherits child's | **built + checked** |
| **plan step / operator** | operator node | `pre -> claim`, `before -> op`, `effect -> claim` | `chosen`, `unmet`, `waits_for`, `ready`, `done`, `discrepancy` | **built**, `corpus/planning_execution.cnl` |
| **plan** | — *no node* | (implicit: the set of ops sharing `chosen`) | — | **gap**, §6.2 |
| **procedure** | procedure node | `step -> op`, `step_before -> op` | via its ops | **built**, `corpus/procedure.cnl` |
| **question** | `goal` | `wants -> knowledge-claim` | same as goal | **built + checked**, `meta_concept_unification_experiment.py` |
| **prohibition** | ordinary fact | `forbidden`/`dangerous` on the candidate | — (consulted as negative premise) | **built + checked**, `prohibition_rules.py` |
| **stance (open/closed world)** | ordinary fact | `actively_verify` on the concept | — | **built + checked**, `nac_verification_experiment.py` |
| **call / proposal** | `<call>` | `tool -> T`, `arg -> node` | pending / consumed | **built**, `ugm/dispatch.py` |
| **rule** | `<rule>` | `rl_head`/`rl_lhs -> <cond>`, `k_subj`/`k_pred`/`k_obj` | — (lifted by `expand_rules`) | **built**, `ugm/learner.py` |
| **hypothesis** | `<hypothesis>` scope | relativized in-scope atoms | ⚠ *verdict is a Python `SupposeResult`, not a fact* | **partial gap**, §6.1 |
| **metarule application** | — *no node* | — | — | **gap**, §6.3 — the load-bearing one |
| **episode / learned metaprocedure** | — *no node* | — | — | **gap**, follows from §6.3 |

The three gaps are not evenly weighted. §6.3 is the one that blocks the user's actual thesis; the other two
are smaller and partly bookkeeping.

---

## 4. The operations, as signatures

An operation here is a *generic metarule* — one rule, written once, that reads a shape without caring what
the content means (`planning_meta_concepts_arc.md` §5's representation-is-not-execution distinction). The
value of writing them as signatures is that it makes §5's closure check mechanical rather than rhetorical.

| # | operation | reads | mints | built? |
|---|---|---|---|---|
| 1 | **RAISE** | an utterance's `force`; or a `pre` not in `<now>`; or an `actively_verify` stance | `goal` + `wants` | ✅ `goal_rules.py`, GAP-FILL |
| 2 | **DECOMPOSE** | `goal` | `raised -> goal` ×n | ✅ `goal_decomposition_experiment.py` |
| 3 | **ORDER** | `step_before` | `before` | ✅ `corpus/procedure.cnl` |
| 4 | **INVOKE** | `<run> proc P` | `chosen` per step | ✅ `corpus/procedure.cnl` |
| 5 | **BLOCK/UNBLOCK** | `pre` vs `<now>`; `before` vs `done` | `unmet`, `waits_for` (+ drops) | ✅ `planning_execution.cnl` |
| 6 | **READY** | `chosen` ∧ ¬`unmet` ∧ ¬`waits_for` ∧ ¬`done` | `ready` | ✅ (privileged — Gap B) |
| 7 | **DISPATCH** | `ready` | `<call> tool act` | ✅ (ungated — Gap A) |
| 8 | **FOLD** | serviced `<call>` result | facts in `<now>`, `done` | ✅ `ugm/dispatch.py` |
| 9 | **RESOLVE** | `wants` claim settled true/false | `achieved` / `diverged` | ✅ `goal_rules.py` |
| 10 | **DIVERGE** | step `done` ∧ no anticipated branch matched | `discrepancy` | ✅ `corpus/procedure.cnl` |
| 11 | **REPLAN** | `discrepancy` | new `chosen` (via RANK) | ✅ `corpus/procedure.cnl`; RANK cost facts in `corpus/planning.cnl` |
| 12 | **VETO** | `forbidden`/`dangerous` matching a candidate | *(nothing — blocks 7)* | ✅ `prohibition_rules.py` |
| 13 | **SUPPOSE** | a claim to assume + a prediction | `<hypothesis>` scope + in-scope derivations | ⚠ verdict not a fact (§6.1) |
| 14 | **COMPILE** | authored content (`X causes Y`, a `define` schema, a co-occurrence) | `<rule>` rule-data, lifted by `expand_rules` | ✅ `ugm/learner.py` |
| 15 | **SELECT** | candidate set + preference facts | a `chosen`/commitment | ⚠ partial — RANK exists for *ops*, nothing for *metarules* (§6.3) |

Fourteen of fifteen exist. That is the genuinely encouraging finding of this write-up, and it is consistent
with the arc's own repeated result — the machinery keeps turning out to already be there. The exception,
15, is exactly the one the user's framing says determines effectiveness.

---

## 5. Why this composes to unbounded depth — a closure argument, not a sample

`cnl_engine_goal_plan.md` phase C established the right standard for this project: an induction, not a
sampling of nested cases (and `smt_sieve.py` runs the base case and inductive step for the connective forms
for real). The same standard applies here, and the argument is simpler than the forms one because the
carrier is uniform.

**The claim.** Let *V* be the vocabulary of §3 (the node kinds) and *Ops* the operations of §4. For every
operation, every node it *mints* is of a kind already in *V*, and every node it *reads* is of a kind already
in *V*. Therefore the set of reachable structures is closed under *Ops*, and an arbitrarily deep composite —
a procedure whose step is a question whose answer requires a hypothesis about another procedure — is not a
new structural case. It is the same table, applied again.

**Read straight off §4's table**, this is checkable rather than asserted:

- 1, 2 mint `goal`. In *V*.
- 3, 4, 5, 6 mint step lifecycle attributes on operator nodes. In *V*.
- 7 mints `<call>`. In *V*. 8 folds a result into ordinary claims — the open class, which every `wants`
  and every `pre` already points at.
- 9, 10, 11 mint lifecycle attributes and `chosen`. In *V*.
- 13 mints a scope containing relativized copies of *V*-shaped nodes — closure preserved by relativization,
  which was the entire point of `scope-reframe-relativization`.
- 14 mints `<rule>`, which the fixed lifter turns into an executable rule that itself is an *Ops* member.
  **This is the one genuinely reflexive edge**, and it is what `computation-model-not-llm` names as the
  actual advantage: the closure is closed over rule-creation too, not merely over data.

**The four depth cases the arc actually worried about, resolved by the same closure:**

| case | why it's not a new structural case |
|---|---|
| procedure whose step is a question | 2 applied to a step node; a question *is* a goal (§3) |
| question about a procedure | an ordinary read of `step`/`step_before` — data, never execution |
| action blocked by a standing rule | 12 is a negative premise on 7; order-independent, checked |
| hypothesis about a plan's readiness | 13 relativizes 6's inputs; `chain_sip` walks the declared readiness rules (this is precisely why `metaprocedure_model.md` §1b insisted 6 stay a *declared* rule) |

**What this argument does *not* buy, stated so it isn't over-claimed.** Closure gives *well-formedness* at
any depth. It gives neither **termination** (14 and transitivity are recursive; `STATUS.md` phase D is
still untouched, and the surge detector still cannot distinguish convergent recursion from a runaway cycle)
nor **consistency** (two branches concluding incompatible things is detected by `detect_conflicts()` but
arbitration is still undeclared — `planning_meta_concepts_arc.md` §7). Those are real and separate. The
honest claim is: depth is structurally safe; depth is not yet *bounded*, and conflicts at depth are
detected but not resolved.

---

## 6. The three gaps, in increasing order of importance

### 6.1 A hypothesis's verdict is not a fact

`suppose()` builds a real `<hypothesis>` scope with real relativized in-scope atoms — the representation
is genuinely there. But its verdict (CONFIRMED / REFUTED / INCONCLUSIVE) comes back as a Python
`SupposeResult` and the scope is then retired. So no rule can react to "that hypothesis was refuted," which
is exactly the asymmetry `goal_machinery.md` §2 already resolved for goals by making the outcome a positive
fact. The fix looks small and precedented: mint `refuted`/`confirmed`/`inconclusive` on the `<hypothesis>`
node, and keep the node after the scaffolding is retired. Worth checking whether retiring the scaffolding
currently takes the node with it.

### 6.2 There is no plan node

A plan today is implicit — whichever operators happen to carry `chosen`. That works for one plan, and
breaks the moment two candidate plans should be compared before committing, which is precisely what
`planning_meta_concepts_arc.md` §1's explore-then-commit boundary describes. A plan node (`plan` with
`includes -> op` and its own lifecycle) would let a whole plan be hypothesized, ranked, and committed as one
thing. Lower priority than 6.3 but it is what 6.3's SELECT would want to range over.

### 6.3 A metarule application is not a node — and this is the one that matters

Right now, applying a metarule is invisible. A rule matches during `revive()`, fires, and the only trace is
its output. Nothing in the graph says *this operation, was applied, to this goal, at this point, and it led
here.* Four things the user's framing asks for all fail on this single missing node:

- **Choosing** among metarules requires candidates to point at. There is no candidate node, so today the
  answer is "everything applicable fires" — which is `run_bank`'s blind fixpoint, the exact weakness
  `metaprocedure_model.md` §1 set out to replace. Note RANK/REPLAN already do preference-based selection —
  but over *operators*, not over metarules. The mechanism exists one level below where it is needed.
- **Non-greedy** choice requires lookahead, which means hypothesizing an application before making it —
  which requires the application to be a thing that can be supposed.
- **Recording** what worked requires an episode: an ordered set of applications that closed a goal.
- **Learned metaprocedures** then need *no new representation at all*, and this is the payoff worth stating
  precisely: **if a metarule application is a node, then an episode is a sequence of them, and compiling an
  episode into a reusable metaprocedure is operations 2+3 — decompose and order — applied to application
  nodes instead of to domain steps.** A learned metaprocedure is just a procedure whose steps are metarule
  applications. `ugm/learner.py`'s COOCCURRENCE rule is already the precedent that an ordinary rule can
  write rule-data from observation; this would be that same shape aimed at applications.

Which is to say: the whole "learned metaprocedure" ambition reduces to one missing node kind, and reduces
to *nothing else new*. That is a strong enough claim that it should be probed rather than believed.

---

## 7. Probes — RUN, 2026-07-30. Results first, then the original plan.

**All three built and green, but two of them only after a first run failed, and both failures are more
informative than the passes.**

**Probe A — closure (`units/closure_probe_experiment.py`).** Harvests all 37 `StandingUnit`s across
`units/` by introspection and checks that every minted node kind is a kind some rule can match. Result:
10 distinct kinds minted, **zero dead ends**, all roles walkable, 5 unread kinds all classifiable as
open-class content. ⚠ **The first version passed vacuously** — it treated `identity_rules.py`'s
`name=AttrVar("nm")` as a wildcard reader and short-circuited to green. It is a *co-reference* constraint
("two nodes whose names are equal"), not a universal reader, so it was credited wrongly and the check never
ran. A false green is worse than a red; fixed, and the check is now real. Secondary finding: **no rule in
any `units/` rule library mints rule-shaped data** — the reflexive edge is proven in
`tests/units/test_engine.py:1211` but has never been promoted into a shipped library.

**Probe B — application-as-node (`units/application_node_probe_experiment.py`).** Four checks, all green:
a generic audit rule matches applications without knowing which operation ran; the application's `of:`
edge lands on the **real `StandingUnit` node** (identity-compared against `rule.node`), not a name string —
so applications are homoiconic, not a parallel logging vocabulary; two operations on one goal are
distinguishable; and a *prospective* application can be supposed, reasoned over in-scope, and leaves the
world untouched. ⚠ **The lookahead check was a false green on first run.** Wiring the supposition and the
reflective axiom to the *same gate* meant one delivery silently replaced the other, and the "reasoned over
the prospective application" result was actually the two real applications. **General finding, worth
promoting: two sources on one gate do not compose — `view()` composes across gates, never within one.**
`goal_machinery.md` §4's "wire every source that's needed" is necessary but not sufficient.

**Probe C — episode → procedure (`units/episode_to_procedure_probe_experiment.py`).** Green: an episode is
recorded with recoverable order, compiled into one `procedure` whose steps are the operations applied, and
that learned procedure runs on a fresh goal, marking its operations `chosen` — the same fact a
hand-authored procedure produces, so learned and authored converge on one executor. **Two corrections that
weaken §6.3's claim and should be carried forward:**

1. **Applications minted in one settle have no inherent order.** Rules in one `revive()` do not fire in a
   defined sequence and a minted node records no timestamp, so an episode harvested from applications
   alone is an unordered *bag*. Fixed by having the **outer driver** stamp a turn marker each turn, which
   is legitimate (that layer correctly holds stepping state per §1a) but must be stated: episodes are only
   as ordered as the driver makes them, and two operations applied in the same turn are irreducibly
   unordered.
2. **"Compiling an episode is just DECOMPOSE" was too strong.** The first version minted ten procedures
   with one step each, because `Emit` mints fresh per firing. It is DECOMPOSE **plus the same interning
   guard** subgoal-raising needs (`goal_machinery.md` §2), split into create-once and add-step-once rules.
   Both guards are ordinary `absent(...)` — nothing new *in kind*, which is the claim that survives — but
   "no new machinery" is not the same as "no new rules," and the original wording blurred that.

**Net verdict.** §6.3's cascade is unblocked and the payoff is real: a learned metaprocedure needs no new
*representation* and no engine work. It does need two ordinary interning guards and an externally supplied
ordering source, neither of which was in the original claim.

---

## 7b. The probes as originally planned

**Probe A — closure, checked mechanically rather than argued.** Encode §3's *V* and §4's signatures as data
and assert that every operation's mint-kinds ⊆ *V*. This is cheap, and it converts §5 from prose into
something that *fails loudly* when a future operation is added that mints something outside the table —
which is exactly the discipline `sieve.py` already provides for the forms. Do this first; it is the
cheapest and it guards everything after.

**Probe B — application-as-node, minimal.** Mint an `<application>` node when a metarule is applied, with
`of -> rule`, `on -> goal`, `at -> turn`. Check three things: an ordinary rule can match it; a `suppose()`
can reason about a *prospective* one; and two applications on the same goal are distinguishable. If this
holds, 6.3's whole cascade is unblocked.

**Probe C — episode → procedure.** Given a goal that reached `achieved`, and its applications, apply
operations 2+3 to mint a procedure whose steps are those applications, and confirm operation 4 (INVOKE) can
run it on a fresh, structurally-similar goal. This is the actual claim of §6.3's payoff, and it either
composes with no new machinery or it doesn't — a binary outcome, which is the kind this arc has done well
with.

**Probe D — hypothesis verdict as fact** (§6.1). Independent of B and C; small; do it whenever.

Probe A before B before C. Nothing here needs the closed algebra to change, and per the arc's standing
discipline the expectation should be a surface slice, not engine work — with the honest caveat that §6.3
is the first item in a long while where that expectation has *not* already been confirmed by something
adjacent, so it deserves genuine skepticism until Probe B actually runs.

---

## 8. The graph-database test — a falsification bar, not a porting plan

Raised in conversation while this document was being written: *if this were properly formalized, you could
almost run the engine on an ordinary graph database.* This is worth recording precisely, because its value
is **not** as an implementation proposal. It is the sharpest available test of whether §5's closure claim
is real or merely stated. Prose can hide an unstated dependency indefinitely; a Cypher (or SPARQL) target
cannot, because anything the model actually needs that the query language does not have shows up
immediately as a thing you cannot write.

**What ports cleanly, and why that is unsurprising rather than impressive.** The closed algebra maps almost
one-to-one onto what a property-graph query language already does natively: conjunctive matching is a
`MATCH` pattern; the five substrate effects are `CREATE`/`MERGE`/`SET`/`DELETE`; negation-as-failure is
`WHERE NOT EXISTS`; the band meet is an attribute plus a `min` aggregate, and the θ gate is a `WHERE`
threshold. Every concept in §3's table is nodes and role edges by construction — requirement 2 of §2 exists
precisely so that nothing is packed into a structured value a query language would have to unpack. Rules
themselves port too: they are already flat graph-resident data (`rl_head`/`rl_lhs`/`k_subj`), so the
"lift" step becomes *generate a query from rule-data* rather than *build a `Rule` object*.

That much genuinely would work, and it is a real endorsement of the representational discipline. But the
matching was never the hard part, and it would be a mistake to read a successful port as validating more
than it does.

**What does not port, stated honestly — and each item is informative about where the engine's real content
sits.** Four things, in increasing order of how much they matter:

1. **Fixpoint.** A graph query language evaluates one query; it does not run rules to a fixpoint. You would
   need an outer driver loop, which is fine — that loop is `metaprocedure_model.md` §1a's correctly-Python
   VM anyway. Not a real obstacle, but it means the DB is the *matcher*, not the engine.
2. **Demand-driven evaluation and focus bounding.** `chain_sip`, `ask_goal`'s `focus_scope`, and
   `reactive.py`'s per-predicate opt-in all exist to *avoid* exhaustive completion — the "agent, not
   theorem prover" stance. A DB backend gives you eager whole-graph matching, which is exactly the posture
   this project has repeatedly and deliberately rejected. You could rebuild demand-driving on top, but
   you would be reimplementing the part that carries the design commitment.
3. **The gate/tunnel discipline.** A `StandingUnit` sees only what is delivered to its gates, never the
   ambient graph (`units/engine.py` invariant 3), and `goal_machinery.md` §5's twice-confirmed finding —
   that a rule's output carries only what it minted, not what it merely read — is a *consequence* of that.
   A DB query has ambient access to everything by default. This is not a missing feature to add; it is a
   deliberate restriction that would have to be re-imposed, and much of §3's checked behaviour depends on
   it holding.
4. **Conflict detection.** `detect_conflicts()` (`units/engine.py:853`) surfaces two rules concluding
   incompatible things as an ordinary fact on a wire rather than letting one silently overwrite the other.
   A DB gives you last-write-wins. Since `planning_meta_concepts_arc.md` §7 makes runtime conflict
   detection the *whole* answer to open-middle-tier composition safety, losing it would remove the
   mechanism the composition argument rests on. This is the one item that is genuinely load-bearing rather
   than merely inconvenient. (Note it is currently a `units/`-side mechanism; whether `ugm/` has an
   equivalent is unchecked and worth knowing independently of this section.)

**The useful conclusion.** Items 1 and 2 say the DB would be a matcher under a driver, which is a fair
description of what a backend should be. Items 3 and 4 say something more interesting: *the engine's real
content is not its matching but its restrictions* — what a rule is prevented from seeing, and what happens
when two rules disagree. That is a genuinely clarifying result to get from a thought experiment, and it
suggests the right use of this idea is as a **specification exercise**: write §3 and §4 precisely enough
that a DB backend *could* be built, use the attempt to smoke out unstated dependencies, and treat any
place where the translation stalls as having found something the prose was hiding. Actually building the
backend is a separate question, and shares the standing verdict of `rust-engine-plan`: firmware first,
port later, and never port something still being designed.

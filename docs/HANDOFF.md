# Handoff — 2026-08-11

Branch `restart`. `main` still holds the old 46-module engine on purpose.

`docs/rules-design.md` is still the design and still the only doc that argues anything. **This file
is a map, not a source** — where it disagrees with the design doc, the design doc wins.

---

## Verify in one go

```
python -m ugm.selftest     240 checks, 0 failing        the runner; any False is a failure
python -m ugm.agreement     28 reads, 12/12 exercised   the rule-level read against the native one
python -m ugm.bundle        17/17 bundled rules exercised  is every shipped rule load-bearing?
python -m ugm.backward       0 failing, 0 blind         backward reading, as the rules that replaced the phase
python -m ugm.compose        0 failing, n steps -> 1    composition, measured
python -m ugm.modality       (table)                    grade vs lifted vs supposed
python -m ugm.workload       0 failing                  can this workload measure recall at all?
```

`ugm.bundle` re-runs the whole suite once per bundled rule; it takes ~20s (it took five minutes
before `theread`).

---

## What happened, in order

The session began by reviewing `rules-design.md` and ended with four of five interpreter phases
gone. Ten commits:

| commit | what |
|---|---|
| `spine` | the doc rewritten around a **floor / bundle** split (1902 → ~2400 lines, now 2999) |
| `stratum0` | the read written as rules; `ugm.agreement` |
| `intake` | `says` becomes a bundled rule |
| `acting` | dispatch moves to the write; `did` and `assert-act` become rules |
| `surprise` | deviation becomes four rules; `ugm.bundle` |
| `supposing` | supposition stops owning the loop |
| `own seat` | reports stop landing inside hypotheses |
| `mention` | mention propagates through bindings; rules can reason about rules |
| `fit` | match as a request; `ugm.backward` |
| `delivery` | the boundary calls in; the tick loses its first line |
| `check` | the second request; backward reading entire, in five rules |
| `handoff` | this file |
| `denial` | §9 settled by measurement: sign **and** `not`, translating one way |
| `compose` | pattern-against-pattern is **unification, not match**; composition built and measured |
| `occasions` | leaving a hypothesis and running out of work become **facts**; callbacks and watchdogs |
| `nophases` | the last phase deleted. `tick()` has no line a rule could have written |
| `recall` | §19's first slice: `prefer(<R>, k)` as facts, a budget, and widening |
| `norms` | §19's carve-out: a prohibition is a **veto at the gate**, never a competitor in recall |
| `naming` | a **fact may carry a name**; a named norm is a node rules can retire |
| `reference` | reference is **binding**; the walk is one order; the naming claim corrected |
| `theread` | the read indexed — **67× on the goal fixture**; and `causes` was orphaning the register |
| `workload` | a workload recall can be measured on — and **recall cannot pay until the agent can stop** |
| `better` | preference **orders** rather than excludes; relevance is derived, not authored |
| `lookup` | *what could produce this?* becomes an **index, not a scan** — 13× fewer ticks to the goal |
| `doubt` | preference is a **score on the grade scale**; doubt is a tie, and a tie needs no threshold |
| `knob` | *close* is a knob, so it is a **fact**: `tolerance(2)`, over a table that carries a **score** |

### 1. The spine changed

The user's challenge: **prove `moment`, `entry` and `sign` cannot be open class.** They cannot. They
are the agent's *internal representation of reality* — teachable, replaceable, and the thing an agent
reasons better by having. So the doc is now four parts: **the floor · the internal representation of
reality · what it allows · gates**, and nearly everything is convention.

The floor is five items on **three grounds**, which matters because flattening them makes all of it
look inevitable:

* **irreducible** — variables+substitution, one total step, the register
* **by guarantee** — the stamp (reducible, but reducible provenance is forgeable)
* **by economy** — ordering (fully reducible; its reduction turns linear matching into subgraph
  isomorphism)

`recall` was never a primitive. Descent to the floor is **grammaticalization** and must be *measured*,
not decided in a sitting.

### 2. The bootstrap is solved

Only one of four steps of applying a rule is circular. **Stratum 0** = rules whose antecedent members
are all structural; they are applied without a read, and the criterion is decided by scanning an
antecedent. Three regresses (reading, selecting, proposing) all escape into **a function, not a
search**.

Consequence worth keeping: stratum-0 rules are ordinary data, so **the read is replaceable at run
time**.

### 3. Four phases left the loop, and each one taught something different

| | |
|---|---|
| **intake** | a phase can hide a **precedence claim** — "runs before any rule" became an authored order a corpus can override |
| **acting** | it was in the wrong place *and the doc already said so* (§16 puts dispatch at the write). `<assert-act>` made §18 concrete: delete it and the agent still acts, still knows it acted, but no longer assumes success |
| **surprise** | a branch hides **how many claims it was making** — one comparison became four rules, three of which nothing could kill |
| **supposing** | the hard part was not the register (3 lines) but a **nested `run()`**. Entering is a write, leaving is quiescence |
| **delivery** | **being machinery never made it a phase.** An arrival is an external event; the boundary calls in |

> **A convention hidden in vocabulary is easy to see and cheap to move; a convention hidden in
> control flow is invisible and expensive.** The census counts names, and names were the easy half.

### 4. §5's wall came down in two halves

**Quiescence is a third place the machinery declines, and it declines silently** — §2 named only
match and write. A rule reasoning about rules was dropped as *nothing left to do*.

**Use/mention by authorship was too strong**; the replacement is *mention propagates through
bindings*, checkable because consumed entries are already recorded for the trail.

**`match` from a rule is a request, not a sixth primitive — and it cannot answer with a binding**,
because a rule cannot apply one. *Match and substitute travel together.*

### 5. Two occasions, one mechanism — and the wall was protecting something

Two questions turned out to be one. *What runs on the way back out of a hypothesis?* and *what stops
reasoning dying quietly with a goal still open?* Both want something to happen at a moment the
machinery owns and no rule can name — so both get §17's treatment for arrivals and emissions:
deposit the smallest unarguable record, let rules say what it means.

    left(<frame>, <assumption>)      written by `_leave`, after discharge
    quiet(<m>)                       written by `_wake`, once per seat

**`quiet` closes §5's third silence.** Match and write were the two named places the machinery
declines; quiescence was a third that said nothing at all. It is also the moment an *aggregate over a
finished search* becomes legitimate — which is where §21's homeless `blocked` belongs. A watchdog
needs nothing more: it is an ordinary rule with `+quiet(?m)` in its antecedent, inert until the loop
stops because nothing else writes that. **The trigger is the fact** — no trigger table, no registry.

**A callback is a pointer to a rule, and it may not be a call.** `+resume(h, <R>)` hangs a rule on a
hypothesis; `<resuming>` picks it up and can only say *this rule's turn has come* (`+due(<R>)`),
because §5 forbids a rule applying a rule. A `dormant` rule is not proposed by ordinary recall; a
`due` one is. So a callback is **directed recall, not invocation** — and that is stronger than a call:
the woken rule still has to match, can still be defeated, still competes, still yields to a surprise.
Adding continuations did not weaken *nothing owns the loop*.

It also lands on §19's reserved seam: `dormant`/`due` are the first thing a corpus has ever been able
to say to `_recall`.

Three things this cost, and two of them were bugs that had been invisible:

* **substitution was minting twins.** Rebuilding a consequent goes through the interning constructor,
  so descending into a rule node returned an interned *copy* — the pointer named a rule that did not
  exist and every question about the real one answered nothing. Fixed in `substitute`/`ground`: a
  subterm nothing changed is returned unchanged.
* **mention had no source.** §14's *mention propagates through bindings* needs somewhere to start; a
  rule authored naming a rule (`<...>` in its consequent) is it. Without it a rule attaching a rule
  was dropped by quiescence as *nothing to do*.
* **the occasion persists.** `quiet` is an entry, not an event, so a watchdog is armed from quiescence
  onward, not fired once. One whose conclusion re-arms it runs to its budget. Likewise `due` is not
  consumed — a woken rule stays awake, which is fine only while recall is exhaustive.

### 6. The last phase went, and the count is zero

`_expand_goal` is deleted. `tick()` is now recall → match → defeat → quiescence → arbitrate → apply,
plus the two things a register owes: `_leave` when a hypothesis runs out of work, `_wake` when the
loop does. **There is no line in it a rule could have written.**

Backward reading ships as five bundled rules over three requests — `<ask-fit>`, `<plan>`, `<expand>`,
`<ask-check>`, `<give-up>`. What made the last one possible is the `verdict` request: `blocked` claims
that **no** rule fits, an aggregate over a finished search, and `quiet` is the fact that says a search
has finished. The machinery answers it by counting `fits` and `achieved` entries **the rules
produced** — it runs no search, so *which rules were considered* stays recall's business.

Two supporting changes:

* **rules are data when authored** (`RuleSet.on_rule` → `Machine.reify`). Backward reading enumerates
  `+rule(?r)`, so a rule loaded after someone called `reify_all()` was invisible to it with nothing
  reporting so. `reify_all()` is kept and idempotent.
* **R2 moved from the licence to the trail.** The phase stamped subgoals `wanted`; now `<expand>`
  writes them, so the licence is `applied(<expand>)` and the reading is recovered one hop back —
  `<expand>` consumed a `need` entry, and `_fit` licences everything it answers `wanted(<R>, goal)`.
  Checked by walking the trail rather than by trusting a stamp.

**What it cost, measured.** 98 steps where the phase took ~10 on the same corpus; `ugm.backward`'s
fixture is 194 steps / 411 writes. `ask-fit` asks every reified rule about every goal, which is
exactly what §19 exists to narrow — the phase hid that cost by hard-coding the narrowing.

**Two gaps this made visible, neither of them new:**

* **a root goal is never checked** for satisfaction. `<ask-check>` keys on `subgoal(plan, ?w)`, and
  *a goal with no plan* is not expressible. Checking every goal binding-free would reintroduce §18's
  sibling failure, so this needs a real answer, not a rule.
* **a request can only be made once.** `<ask-check>` asks when the subgoal appears; if forward
  reasoning satisfies it three ticks later, nothing asks again, because re-concluding `+check(p, w)`
  changes nothing and quiescence drops it. This is why `ugm.backward`'s historical 29th fact
  (`achieved(water(kettle))`) is no longer produced — recorded there as a claim about the phase, not
  as a current output. A re-ask needs a fresh request node; §21.

### 7. Recall stops proposing everything

§19's seam is open. `prefer(<R>, k)` is a table of **ordinary facts** — *when `k` is in play, bring
`R` to mind* — authored for now, learnable later from the trail R5 already deposits. `recall_budget`
is `None` by default, so behaviour is unchanged until a corpus claims something.

**The key is not the register.** Attention *is* the register (`Machine.focus`, a `Frame(seat, topic)`
— §4's one privileged pointer), and that is why it cannot be the key: a seat is a fresh moment every
tick, so a table keyed on it never sees the same key twice. The key is **a relation in play**
(`_in_play` = the relations in the current moment's delta — *what just changed*). That is one method
wide, deliberately; a better key replaces it without touching the loop, the table, or any rule.

**A shortlist that ran dry is not a search that finished** — and this is a *soundness* condition, not
a quality one. `<give-up>` asks its verdict at `quiet`, and `blocked` is an aggregate over a finished
search. So quiescence under a budget escalates to the exhaustive pass first (`_widen`, step state
`widened`), and only its silence writes `quiet`. Take the line away and the same corpus gives up on a
goal it can reach — checked, and the check is shown able to fail.

**Randomness was considered and not taken.** §3 forbids reading a derived result out of a set, and an
unseeded top-K draw is that bug wearing a hat: two runs diverge and the trail records neither the
choice nor the reason. The tie-break is authored order, the same one arbitration uses. If exploration
is what randomness was for, §19 already has the better answer — the exhaustive pass on novelty or a
schedule, which injects what a draw *from the shortlist* structurally cannot.

### 8. Norms come off the recall path

§19's carve-out, and it is the one place the design refuses to be incomplete:

> Recall may be incomplete about what to do. It may not be incomplete about what you must not do.

`forbidden(<pattern>)` is a norm. Its argument is a **description** — `forbidden(doing(harm(?x)))`
names a class of acts the way `ant(<R>, heat(?a, ?w))` names a class of premises. It is never
proposed, matched or arbitrated: `Gate.veto` consults it on every write, **before the deposit**, so a
forbidden entry never exists — not even briefly, and not for an `on_write` hook to see. Dispatch *is*
an `on_write` hook, so that is what keeps the act inside the agent instead of emitting it and
regretting it.

Cheap because it is indexed by what is about to be written (§3's instances-by-relation): only norms
whose pattern shares the proposition's relation are resolved.

**A refusal writes.** `refused(p, sign, <norm>)`, licensed by the norm. A veto that deposited nothing
would be a fourth silent decline, and silence about norms is the exact failure being designed against.

Three things fell out rather than being arranged: quiescence still terminates (the *refusal* is what
stops the rule re-applying — otherwise a norm is a livelock); a norm forbids `+` only, because
bringing about is asserting; and a norm is still an ordinary belief, resolved at the writer's own
position.

### 9. Naming a statement, and what it separated

Stating a norm was not enough. A norm's argument is a **description**, a description is an authored
statement, and §8 scopes a statement's variables to it — so `forbidden(doing(harm(?x)))` written twice
is *two nodes that say a similar thing*, and denying the second leaves the first forbidding, silently.
**Restating is not revising.** That is §8's own rule about rules arriving somewhere it had not been
noticed.

The repair was already in the surface. A fact may carry a name:

    fact <no-harm> = forbidden(doing(harm(?x)))
    fact -<no-harm>

`<...>` is the namespace of **statements**, and a rule is a statement — so it is one table, not two.
A rule and a norm sharing a name would be two things with one name, which is what the marker exists
to prevent.

A separate consequence, about the carve-out rather than about naming:

> **§19 keeps norms out of recall. It never said they were beyond argument.**

A rule can retire a norm on evidence — `{+says(fire, evacuate, +)} ⟹ {-<no-harm>}` — trail intact,
with the refusals it made beforehand still on the record. **Unconditionally consulted** and **entirely
contestable** are different properties.

⚠ **Naming is not what separated them.** Measured afterwards: a rule could always do this *without*
the name, by describing the norm's shape — matching a generic antecedent against a stored description
treats the description's variables as ordinary nodes, so `?y` binds to the stored `?x` and
substitution rebuilds exactly the node written. Naming buys **authoring** (a second surface statement
about one description) and a handle for facts that are not about its shape. It never bought
reference.

Forced, not chosen: a rule may conclude about a named fact and a named fact may be about a rule, so
the loader does three passes — name what is self-contained, then rules, then everything else. A name
needs only its node, and a statement referring to no other statement can be built without one.

### 10. Reference is binding, and the walk was two orders

The question was *what else wants a name — a supposition, a plan?* Answer, measured: **mostly nothing
does.** A plan, a hypothesis, a rule and a norm are all referable already, because anything deposited
as an entry can be bound by an antecedent, and **binding is reference**. Language works the same way —
it says *the plan we made before*, not a name. Names are for the exceptions.

What binding does not supply is **which one**, and that turned up a live bug. Several entries match
one description; the walk decides which is tried first, and the walk disagreed with itself:

* `Moment.ancestors()` — newest moment first
* a moment's `delta` — oldest entry first

So two candidates deposited by `implies` (same moment) came out in the *opposite* order to two
deposited by `causes` (different moments) — and which connective a rule used has nothing to do with
reference. One `reversed()` in `current_state` makes it one order throughout, and *a description
resolves to the most recent* is now a claim with a check behind it instead of an accident.

⚠ **It changed a result, and the change is the finding.** `ugm.backward`'s sibling-agreement fixture
flipped: with the taps authored one way the plan now succeeds, the other way it still blocks. Same
world. Because:

> **Reference resolves to the most recent, and nothing reconsiders.** `_settle` takes the first entry
> that satisfies a subgoal and never returns to it. Checking siblings inside the plan's bindings stops
> a wrong plan being reported as a good one; it does not *find* the right one.

`ugm.backward` now runs both orders and prints both outcomes — §21's backtracking item measured rather
than asserted. And the old fixture was, it turns out, measuring the walk order rather than the
guarantee.

**One bug fixed on the way**: `discharge` dropped `mention` when carrying a conclusion out of a frame,
so a conclusion *about a rule* drawn under a hypothesis was refused by the gate — §14's propagation
with a hole in it at the one place conclusions change hands.

### 11. Where the cost actually was — and it was not recall

The question was *what is load-bearing for a working system — recall, learning?* Measured first, and
the answer was neither.

The goal fixture is an n-rule forward chain with one goal at the end:

| rules | before | after |
|---|---|---|
| 2 | 1.56s | 0.07s |
| 4 | 7.00s | 0.19s |
| 8 | 54.9s | 0.82s |
| 16 | ~7 min | 4.68s |
| 32 | — | 37.1s |

**67× at n=8.** `ugm.selftest` went 19s → 1.8s; `ugm.bundle` five minutes → 19s. Nothing about the
semantics changed, and 208 checks agree.

**The first attempt was wrong and is worth recording.** The obvious read of the cost was *recall is
exhaustive*, so recall became a request (`+recall(g)` → `+recalled(<R>, g)`) to make narrowing reach
inside an antecedent. It made the default **twice as slow** and broke a soundness check. Profiling
afterwards:

* `chain.resolve` — **86% of runtime**, 415k calls
* `current_state` — called **2043 times for 123 steps**: once per rule per tick, rebuilding and
  re-resolving the entire state each time

So three changes, each measured before the next:

1. **the walk, once per tick** instead of once per rule (`match` takes the state) — 8.6×
2. **the state, indexed by (sign, relation)** — an antecedent member with a fixed relation no longer
   unifies against every entry. §3 gives the substrate exactly this index and the argument was just as
   true of the state, where nobody had made it. A bare-variable member still scans everything, which
   is correct — `+?p` genuinely is about anything.
3. **the read, indexed by proposition** — `resolve` scanned every entry ever deposited to answer a
   question about one. Now it scans that proposition's entries, which are almost always one. The two
   orderings (latest locus, then latest deposit) become a single comparison on
   `(locus.depth, seat.depth, position)`, and containment still costs a real ancestry test because a
   depth comparison cannot survive a fork.

⚠ **`_recall` narrowing cannot reach an antecedent, and that stands.** `<ask-fit>` matched **72 ways**
in one tick with four domain rules. Recall narrows which rules are *proposed*; a cross product in an
antecedent is unaffected. The recall-as-a-request branch is stashed, not deleted — but it is not
needed for cost any more, and it should only come back with a measurement behind it.

⚠ **A bug the fixture found while trying to measure something else.** Applying a `causes` rule minted
a **fresh frame**, dropping the parent, purpose and wrap. Under a hypothesis that orphaned the
register: `_leave` could never fire, the frame was never discharged, and everything concluded under
that hypothesis stayed inside it with nothing saying so. §4 allows one register; advancing it is a
*seat move* (`Gate.reseat`), not a new frame. Discharge then needs the frame's **origin** rather than
its current seat — those stop being the same thing the moment it moves, and reading it off `seat`
carried out only the last moment.

The index is gated against a brute-force walk over a world that forks and revises — 2448 comparisons,
because replacing a walk with an index is exactly the change that is right for a fixture and wrong for
a fork.

### 12. A workload recall can be measured on — and what it measured instead

The question was *how do we build a big enough workload; should we take `../pystrider`?*

**Not from pystrider's rules.** `pystrider/rules/*.mf` are microfunctions — `ATTR`, `CONST`, `JMPNOT`,
`DISPATCH` — the ISA-with-opcodes floor this design rejects, and CLAUDE.md is explicit that nothing is
ported without re-deriving it. It is 532 lines, so it is not "big" either. What *is* worth taking is
the shape of `experiments/vocabularies/` — business, ux, bridge: **separate worlds that must be
joined**. (Two memories warn against pystrider; both are about *gating* on it as a consumer of the old
engine, which this is not.)

**Size was never the problem.** On a 30-rule chain, between one and eight rules match per tick — and
since `theread` indexed the state, a rule that does not match costs almost nothing. A perfect table
could not beat exhaustive recall there at any n.

> **A shortlist pays only where many rules MATCH and are useless.** Scale is not the requirement;
> **selectivity** is.

So `ugm.workload` builds D domains × depth R, all seeded, one goal in one domain — every domain's
rules match from the first tick, and D−1 of them are irrelevant. And its first result was that an
ideal, hand-authored table bought **nothing**:

```
  D  R   recall                   ->goal  ->quiet  w@goal  writes
  8  8   exhaustive                  734      801    1798    1873
  8  8   budget 8, no table         1468     1601    1798    1873
  8  8   budget 8, ideal table         8     1593     346    1881
```

The table is **perfect** — it reaches the goal in exactly R ticks, 92× fewer, with 5× fewer writes.
It was invisible because the `->quiet` column is the same for all three:

> **Recall cannot save work in a machine that runs to quiescence.** Narrowing changes the ORDER in
> which everything is done, not how much is done. The prize is real, and only an agent that can
> **stop** collects it.

So the thing in front of learning is not a bigger corpus. It is a reason to stop — and that is the
same question as *when is a plan settled*, *when is a `due` rule done*, *when may a request be
re-asked*, and §21's backtracking. Four hats, one head.

⚠ Two things `ugm.workload` is not. The table is a **ceiling, not an algorithm** — authored, naming
the answer, learning nothing. And its gate is that the table must buy something: if it ever stops
doing so, the workload has become the n-rule chain again with more rules in it.

⚠ **`_in_play` is the wrong key for goal-directed work.** It keys on what just changed, and in this
workload every domain is always in play. The key that would work here is what the agent is *trying to
do*. The hand-authored table sidesteps it by naming each rule's own antecedent relation.

### 13. Choosing the better move — where it belongs, and what it isn't

The framing that started it: *recall should lead the agent to choose better rules instead of doing
dumb things — given many applicable rules, choose the best.* Cost was the wrong lens; a bad choice on
an irreversible step is a mistake, not a slowdown.

**Relevance was already computed and thrown away.** `_fit` writes `fits(<R>, w)` — *this rule could
produce what you want* — and nothing used it. `<relevant>` turns it into a preference in one bundled
rule, so **means-ends analysis is data**, and an agent that should not prefer the rules serving its
current goal deletes it.

Two negative results, each found by breaking something, and both are the same shape:

* ⚠ **Preference must order, not exclude.** Filtering recall by goal-relevance starved
  `{+blocked(heat(?a, ?w))} ⟹ {+doing(heat(anna, ?w))}` — the most useful rule in that corpus, which
  does not fit the goal at all. *Relevance to a goal is silent about everything it is not about.*
* ⚠ **The apparatus is not a competitor.** Let loose over everything, preference outranked the rules
  that notice a **surprise**, so the agent pursued its goal while a channel was saying the world had
  moved. `standing` — a fact, deposited for each bundled rule — keeps the apparatus in its authored
  place. This is §19's carve-out for norms arriving a second time: *being overridable and being
  forgettable are different properties.*

So arbitration now sorts on **authority (defeat) → apparatus → helpfulness → authored order**, and
what preference replaces is worth naming: the tie among applicable, undefeated rules used to be broken
by *the order they happened to be written in*. Still total, still a lookup that never searches; with
no preferences it is exactly the authored order it always was.

⚠ **No end-to-end win yet, and the blocker is measured.** On the workload the goal still arrives at
tick 751, because:

```
  applications: bundled = 752   corpus = 64        (ask-fit alone: 711)
```

`<ask-fit>`'s antecedent is over `rule(?r)` — *every* rule — so it matches |rules|×|goals| ways and,
being standing, monopolises arbitration until backward reading is exhausted. **The phase's precedence
claim survived its deletion, as authored order**: `ugm.backward` measured "the phase starves forward
reasoning" as the phase's sin, and it moved rather than went. Fixing it is pickup item 2.

⚠ `ugm.bundle` caught `<relevant>` shipping **blind** — 15 rules, 14 exercised — before a check
existed for it. The habit earned its keep again.

### 14. Not scanning all possible options

The standing principle, stated by the user: *the system should not scan all possible options;
experience means I choose the best, or if in doubt among the 2–3 best.* §13's blocker was that
principle being violated in one specific place — `<ask-fit>` asking every rule the agent has about
every goal it holds, before doing anything.

The fix is **not** experience. It is an index:

    RuleSet.by_conclusion     rules keyed by the relation they conclude

§3 gives the substrate one index and argues for it in a line — *a rule whose antecedent names a
relation has to start somewhere, and scanning every node is the alternative.* Read backwards the same
argument holds of the rule set, and nobody had made it there. So *what could produce `w0_s8(item)`* is
a **lookup**, and `<ask-fit>` now ranges over what came to mind:

    <ask-recall>   { +goal(?w) }            =>  { +recall(?w) }
    <ask-fit>      { +recalled(?r, ?w) }    =>  { +fit(?r, ?w) }

Measured on the workload at D=8, R=8:

| | before | after |
|---|---|---|
| ticks to the goal | 751 | **57** |
| writes at the goal | 1843 | **458** |
| ticks to quiescence | 801 | **124** |
| `<ask-fit>` applications | 711 | **8** — one per goal |

Exact, not heuristic: a consequent that could produce the goal is in the bucket, and one that could
not was never a candidate. The only rules deliberately absent are those whose consequent is a bare
variable, which §12 already calls vacuous backwards and `fit` already declines.

> **An agent that has to enumerate before it can prefer has not remembered anything.** The index is
> what makes preference affordable; experience then goes on top of it — which of the candidates to
> try first, and when to stop trying.

The gap that is left is honest and small: 57 ticks against an ideal-table 8, all of it forward
reasoning in domains the goal has nothing to do with. That is now the whole of what learning has to
win, and it is the same 7× the workload's gate measures.

### 15. A preference is a score, and doubt is a tie

The user's refinement: *doubt is two or more rules scoring very close, so the table should be a
scoring and not only an order.* Right, and an order genuinely cannot say it — *one clear best* and
*two I cannot separate* look identical to a sort, and they call for opposite behaviour.

**The scale is §10's, reused rather than invented.** A `prefer` claim is an entry, an entry carries a
**grade**, and grades are the ordinal set this design already commits to. So `+prefer(<R>, k) @likely`
outranks the same claim `@possible`, and §12's weakest link applies for free — a preference derived
from a shaky premise is itself shaky, with no second mechanism to keep in step. `<relevant>` now
concludes `@possible`, because *this rule could produce what you want* is candidacy, the weakest
evidence of usefulness there is.

**Ordinal, not numeric, and that is the interesting part.** A cardinal score would be the first such
quantity in the design; §12 says ordinals do not add; and *close* would need a threshold constant
nobody could justify. Ordinals give doubt for free instead:

> **Two rules are close exactly when they tie**, and a tie needs no constant to detect.

`close(<R1>, <R2>)` is deposited when the top score is not unique — pairwise, so the arity is fixed
(§5 refuses a node whose members mean different things depending on how many there are, and *the
candidates I could not separate* is exactly the shape that tempts one).

⚠ **A tie among `standing` rules is not doubt**, and recording it buried the real cases in noise —
19 spurious pairs before the exclusion. The apparatus's order is authored on purpose (read before
acting, notice before continuing); a deliberate precedence is an answer, not the absence of one.

What is deposited and not acted on: arbitration stays total, so the choice is still made. The record
is the difference between an agent that is confident and one that merely proceeds — and what to *do*
when unsure is a claim, so it is rules, and none are written yet.

### 16. *Close* is a knob, so it is a fact — and it is numeric

The user's correction to §15: **closeness is a system knob.** Right. The first attempt got the shape
wrong and they said so — worth recording, because probing it found a defect.

That version declared pairs of grades `indistinct(certain, possible)`. Three things were wrong: it
enumerated pairs instead of saying *within N*; it was a knob on the scale rather than on the
comparison; and **it ignored half the score** — a rule scoring `(certain, 2 votes)` strictly beat one
scoring `(certain, 1)`, so the choice *was* forced, and doubt was recorded anyway.

What replaced it:

    prefer(<R>, key, 3)         the table's row: keyed on a node, matched when that key is in play,
                                carrying a SCORE
    fact +tolerance(2)          a gap of two or less is not a difference I will rely on

Applicable rows sum; two rules are close when their scores differ by no more than the tolerance. Zero
unless claimed, so the default is an exact tie and nothing depends on a constant nobody chose.

⚠ **My first version of this made ordinals add, and the user caught it.** I had the score *be* the
entry's grade, summed — which is precisely what §12 forbids, and I wrote a long apology for the
departure instead of noticing it was avoidable. The score is the **table's own cardinal**, and §10's
grades are a different scale for a different thing, untouched: an entry's grade still composes by
weakest link and no grade is ever added to another. Keeping them apart is what lets
`+prefer(<R>, k, 3) @possible` mean *a strong recommendation the agent is not sure of* — a sentence
one conflated scale would have made unsayable.

Numerals are new in the surface, and cheaply: a numeral is an ordinary atom whose **name** reads as a
number, so nothing in the graph learns arithmetic and exactly one reader wants any.

**Why it must be a fact and not a field: a rule can turn it.**

    rule <care> = implies( { +goal(doing(?p)) }, { +tolerance(4) } )
    fact standing(<care>)

An agent harder to convince when the next step cannot be taken back — *how careful am I being* is a
claim with a trail rather than a threshold somebody chose once. Checked, along with a tolerance too
small to span the gap leaving the choice decided.

⚠ **Being careful has to come before the move it is about**, and nothing orders it that way for free:
the first version of that check failed because `<care>` was an ordinary rule, so the agent committed
and *then* decided to be careful. `standing` is what says otherwise — and a corpus wants it as much as
the bundle does, so it was never a kernel/business distinction.

⚠ Two old friends on the way. `_priority` changed shape twice and a caller kept negating it as the
wrong type. And grade names were being minted with `g.atom` at the point of use — a second node with
one name, the trap this codebase has paid for four times (moot now: the numeric knob does not name
grades at all).

Also fixed while here: recall's ordering used `_rank`, which put `standing` first and filled every
shortlist with apparatus. **`standing` is a claim about precedence once a rule has matched, not about
coming to mind**; recall orders by preference alone.

### 17. Crossing opens hypotheses — and `k` is not a parameter

The user's line: *resist special machinery when the regular wrapping works; we do not need to
duplicate rules, we need a metarule to cross the `likely` and wrap back whatever we concluded — cross,
and handle on resume.* And then: *crossing a `likely` means at least one hypothesis, and two or more
if experience says so.*

That is supposing, and it is built — `<cross>` is `+likely(?p) ⟹ +suppose(?p, likely)`, and
`ugm.modality` already measures it as the winner on every axis (19 rules vs 22 for wrapping written
per-rule; works over rules with variables, which lifting does not; nests; containment structural).

What is new is the second half, and it turned out to need **no mechanism at all**:

> **There is no `k`.** The number of branches is however many `suppose` facts get concluded. Sibling
> hypotheses already work — the forest was built for them.

⚠ **Why one is the right default, as a cost:** one branch per uncertain fact is a frame per
*derivation*, which is linear and is what retired §12's *million moments* objection. Two branches make
n independent uncertainties 2^n. **The first branch is free and every branch after it is exponential.**

Two findings from building it, and they are the same shape twice:

* ⚠ **The alternative must be opened ON RESUME.** Proposed alongside the first, it is enacted while
  the register is already inside it — so it nests instead of branching, and the second case comes back
  wrapped in the first. Keyed on `left(?f, ?p)` they are siblings. The callback mechanism from §5 doing
  the job that most needs it.
* ⚠ **A crossing rule that can match its own output runs away** — 32 sibling frames before the budget
  stopped it, because a discharged conclusion is itself `likely(...)`. §9 records the same trap for
  `<denial>`. The corpus stops it; that it must is a property of self-applying rules.

### 18. Supposing something must not bring it about — and then nothing needs comparing

I said the gap was that nothing **compares** the siblings. The user: *why should they be compared? I
would evaluate whether one hypothesis leads to an unacceptable scenario, otherwise go on.* Right —
that is a veto, not a ranking, and it is a smaller mechanism.

But it has a precondition, and checking it found a serious bug.

⚠⚠ **An act concluded inside a hypothesis was actually emitted.** Supposing a premise whose rule
concludes `+doing(fire(missile))` **fired the missile.** Not a leak in the chain — the conclusion
stayed inside and crossed out wrapped, exactly as §13 promises. The *boundary* was ignoring the
register: dispatch is at the write (§16) and the write never asked where it was standing.

> **§13's *nothing leaves a frame* was a claim about the chain. Effects are not in the chain.**

Fixed as a condition, not a phase: the boundary asks whether any frame on the path to the root was
entered by supposing, which the forest already records as each frame's purpose.

Also: **`doing` came out of the bookkeeping set.** Every other request stays (nothing carries a
`suppose` or a `fit` out of a frame), but *what I would do under this hypothesis* is the one thing such
a hypothesis is for — as bookkeeping, an agent that supposed a premise and found it would fire a
missile came back knowing nothing at all. What crosses is `likely(doing(...))`, which no dispatch
matches, because the boundary keys on `doing` and a wrapped intent is a claim.

**Blocking the emission was only half of it**, and the first repair stopped there — which stopped the
*reasoning* too, so a plan died at its first action. The user's correction: *actual acting should only
come out as a conclusion, a decision to act; during planning the system should ASSUME an outcome.*

> **Acting is a conclusion. What planning needs from it is the action's assumed outcome, not its
> occurrence.**

So the boundary deposits the same record under a different name — `emitted(x)` when it really left,
`taken(x)` when it was decided under a hypothesis — and one bundled row (`<taken>`) turns either into
`did(x)`, from which §15's `<assert-act>` supplies the assumption that it worked. A three-step plan
now runs to its end inside a hypothesis with nothing done at all. Note which half stays defeasible:
that the act was *decided on* is unarguable; that it *succeeded* is still `<assert-act>`, overridable.

**Substituting the action with its outcome needs no plan machinery.** One rule and one fact per
action — `{+did(?a), +achieves(?a, ?y)} ⟹ {+?y}` — and a two-step plan runs to its end inside a
hypothesis with nothing emitted, carried by the actions' effects rather than the actions.

⚠⚠ Making the *other* half sayable (`overrides(<outcome>, <assert-act>)`, so the call is replaced
rather than also asserted) turned up something the design had assumed without providing: **a corpus
could not name a bundled rule.** Every place the docs say *a corpus can override this* depended on it
and none of it was true — the loader knew only names a corpus declared itself, so the bundle shipped
as data and was reachable only from Python. Fixed: the loader seeds its statement table from
`machine.bundle`, one namespace, so a corpus rule may not reuse a bundled name.

**One relation could not carry both intents.** `overrides` is per *step*, so `<outcome>` matching for
one action defeated `<assert-act>` for every action in that step and an undeclared act lost its
fallback. Per-*binding* does not work either — two rules bind different variables, so their bindings
cannot be lined up. Comparing **evidence** does, and it breaks the case §12 was written for:
`overrides(<why>, <boil>)` defeats a rule sharing no consumed entry with the winner, and must, because
a surprise is a rival answer to the whole situation.

| | |
|---|---|
| `overrides(A, B)` | rival answers to **one** situation — B is out for the step if A matched at all |
| `supersedes(A, B)` | rival answers to **each of several** — only B's applications sharing a consumed entry with an application of A are out |

Evidence is the comparison because the trail already records what each application matched (R5 needs
it), so nothing is measured that was not already kept. Measured: the action with a declared outcome is
replaced by it, and the action without one, in the same step, keeps its fallback.

**And then comparison is not needed.** A branch answers *does this lead somewhere unacceptable*, and
§19's veto already answers it: the hypothesis reaches the prohibition, the write is refused inside the
frame, the refusal crosses out as an ordinary record, and the branch has disqualified itself. Nothing
ranked, nothing weighed. Checked.

---

## The state of the code

15 modules, ~4.7k lines. `chain` `graph` `gate` `rules` `channels` `machine` `text` are the engine;
`selftest` `agreement` `bundle` `backward` `compose` `modality` are instruments; `stratum0` is the rule-level
read.

**No phases remain.** `tick()` is recall → match → defeat → quiescence → arbitrate → apply, plus
`_leave()` when a supposition runs out of work and `_wake()` when the loop does.

**Fourteen bundled rules** ship as data (`Machine._install_bundle`): `intake`, `did`, `assert-act`,
`denial`, four `deviation-*`, `resuming`, and backward reading's `ask-fit`, `plan`, `expand`,
`ask-check`, `give-up`.

**Five write-time hooks**: `_dispatch` (acting), `_enter` (supposition), `_fit`, `_settle`,
`_verdict`. These are Python callables, which is honest debt — §21 records it.

**One veto**: `_forbid`, §19's carve-out. Not a hook and not a rule — it runs *before* the deposit,
which is the whole of its guarantee.

---

## Where I would pick up

**1. A reason to stop.** §12 measured it: an *ideal* recall table reaches the goal in **8 ticks instead
of 734**, and it makes no difference at all to a run that goes to quiescence. Everything downstream —
learning, the composition trigger, any claim that an agent is efficient — is waiting on this and not on
a bigger corpus. It is the same question as *when is a plan settled*, *when is a `due` rule done*,
*when may a request be re-asked*, and §21's backtracking. Four hats, one head.

**2. Experience, now that enumeration is gone.** §14 removed the scan; what is left is genuinely
recall's job and nothing does it: **which of the candidates to try first, and when to stop trying.**
The remaining gap on the workload is 57 ticks against an ideal 8, and all of it is forward rules from
irrelevant domains. `prefer` is derived from `fits` or authored — never from experience — and the
exhaustive pass fires only on a dry shortlist, never on novelty or a schedule.

**3. What to DO when in doubt.** §15 built the noticing — `close(<R1>, <R2>)` is deposited when the
choice was not forced — and deliberately not the response. Think longer, ask a channel, suppose one
and look, prefer the reversible one: all of those are claims, so all of them are rules, and none is
written. Suppositions are the obvious machinery for *suppose one and look* and are not wired to it.
Note the ordering trap: arbitration is total, so the move is already made when the doubt is recorded.
Acting on doubt **before** committing needs something this design does not have.

**Definite reference — which one.** Binding refers; nothing selects. A rule cannot say *the latest*,
and `_settle` never reconsiders a binding it took. That is one question wearing three hats: §21's
backtracking, *when is a plan settled*, and *when may a request be re-asked*.

Also still open, and the same question three ways: nothing says when a plan is *settled*, when a `due`
rule is *done*, or when a request may be *re-asked*.

**2. The composition trigger.** Composition is built and measured (n steps -> 1, defeat inherited).
What is missing is *when*: §4's answer is `compose what has run often and never surprised; decompose
what surprises`, and neither half is wired. `RuleSet.composed_from` already records what each shortcut
collapses, so decomposition knows where to look.

**3. Lifting a modality across a rule** — the last of the four callers of §5's wall with no service.

**Smaller, well-specified:** a seat move is not yet an entry (§17 says every seat move is a write);
write-time hooks are not rules; what a `?` conclusion becomes on the way out of a supposition (§9);
whether a channel reporting a denial should write `says(c, p, -)` or `says(c, not(p))`, and whether
permitting both splits a corpus into dialects; the transpiler sketch in §21.

---

## Two habits worth keeping

**Every gate must delete each rule of the thing it checks, one at a time, and report any rule the
fixture cannot kill.** `ugm.agreement` reported success three times while unable to fail — a revision
written at the wrong locus, a read silently picking the first candidate, a transitive rule needing a
*non-competing* entry in between. `ugm.agreement`, `ugm.bundle` and `ugm.backward` all do this to
themselves now, and it has caught something every single time.

**Commits**: sole author, short lowercase topic word, and **never** a `Co-Authored-By:` or
`Claude-Session:` trailer. Audit with `git log --all --format='%B' | grep -ci claude` — it must
return 0. It does.
